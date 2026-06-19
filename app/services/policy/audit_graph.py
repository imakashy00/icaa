"""
Claim audit pipeline, built as a LangGraph graph.

Flow:

    load_policy_context
            |
    run_deterministic_checks      <- numeric/date rules from PolicyStructuredField (no LLM)
            |
    retrieve_clauses_for_claim     <- vector search, scoped to this policy_id
            |
    run_llm_clause_audit            <- LLM reasons over ONLY the retrieved clauses
            |
    compile_audit_report

Splitting deterministic checks from clause-based (LLM) checks is the core
design choice: things that are pure numbers/dates (sum insured, sub-limits,
waiting periods, copay) are computed in Python from structured DB fields and
are 100% reproducible. Things that require interpreting policy *language*
(exclusion wording, conditions, definitions) go through retrieval + a small,
targeted LLM call -- never the full 40-page document.
"""

from typing import Optional, TypedDict

from langgraph.graph import END, StateGraph

from database import get_session
from llm_client import call_claude_json
from retrieval import get_structured_fields, retrieve_relevant_clauses


class AuditState(TypedDict):
    """
    Shared state threaded through the graph for one claim audit run.

    claim:                  dict of claim facts already extracted from the
                             claim form/discharge summary/bills upstream
                             (diagnosis, procedure, treatment_type,
                             billed_amount, room_rent_per_day,
                             days_since_policy_inception, ...)
    policy_id:               the policy this claim is being audited against
    structured_fields:        loaded from PolicyStructuredField (Node 1)
    retrieved_clauses:         clauses pulled via vector search (Node 3)
    deterministic_findings:    rule-based check results (Node 2)
    llm_findings:              clause-based reasoning results (Node 4)
    report:                    final merged verdict (Node 5)
    """

    claim: dict
    policy_id: int
    structured_fields: Optional[dict]
    retrieved_clauses: Optional[list]
    deterministic_findings: Optional[list]
    llm_findings: Optional[list]
    report: Optional[dict]


# ---------------------------------------------------------------------------
# Node 1
# ---------------------------------------------------------------------------
def load_policy_context(state: AuditState) -> AuditState:
    """
    Loads the pre-extracted structured fields (sum insured, sub-limits,
    copay, waiting periods, permanent exclusions) for state["policy_id"].

    Pure DB read, no LLM call. Raises if the policy hasn't been ingested --
    an audit must never silently run against missing policy data.
    """
    with get_session() as session:
        structured = get_structured_fields(session, state["policy_id"])

    if structured is None:
        raise ValueError(
            f"No structured fields found for policy_id={state['policy_id']}"
        )

    state["structured_fields"] = structured
    return state


# ---------------------------------------------------------------------------
# Node 2
# ---------------------------------------------------------------------------
def run_deterministic_checks(state: AuditState) -> AuditState:
    """
    Runs pure arithmetic/date checks against structured_fields -- no LLM,
    fully reproducible. Each finding is
    {"check": str, "status": "pass"|"fail"|"flag", "detail": str}.

    Extend this function as new deterministic rules are needed (e.g.
    maternity waiting period, specific-disease waiting period, age-based
    copay) -- it's plain Python, easy to unit test in isolation.
    """
    claim = state["claim"]
    fields = state["structured_fields"]
    findings: list[dict] = []

    _check_sum_insured(claim, fields, findings)
    _check_room_rent_sub_limit(claim, fields, findings)
    _check_initial_waiting_period(claim, fields, findings)
    _check_procedure_sub_limits(claim, fields, findings)

    state["deterministic_findings"] = findings
    return state


def _check_sum_insured(claim: dict, fields: dict, findings: list[dict]) -> None:
    """Flags claims where the billed amount exceeds the policy's sum insured."""
    sum_insured = fields.get("sum_insured")
    billed = claim.get("billed_amount")

    if sum_insured is None or billed is None:
        return

    if billed > sum_insured:
        findings.append(
            {
                "check": "sum_insured_sufficiency",
                "status": "flag",
                "detail": f"Billed amount {billed} exceeds policy sum insured {sum_insured}.",
            }
        )
    else:
        findings.append(
            {
                "check": "sum_insured_sufficiency",
                "status": "pass",
                "detail": f"Billed amount {billed} is within sum insured {sum_insured}.",
            }
        )


def _check_room_rent_sub_limit(claim: dict, fields: dict, findings: list[dict]) -> None:
    """Checks per-day room rent against a percentage-of-sum-insured sub-limit, if one applies."""
    room_rent_limit = fields.get("room_rent_limit") or {}
    room_rent_per_day = claim.get("room_rent_per_day")
    sum_insured = fields.get("sum_insured")

    if not room_rent_limit or room_rent_per_day is None or not sum_insured:
        return

    if room_rent_limit.get("type") == "percentage_of_si" and room_rent_limit.get(
        "value"
    ):
        allowed = sum_insured * (room_rent_limit["value"] / 100)

        if room_rent_per_day > allowed:
            findings.append(
                {
                    "check": "room_rent_sub_limit",
                    "status": "fail",
                    "detail": (
                        f"Room rent {room_rent_per_day}/day exceeds the allowed "
                        f"{allowed:.2f}/day ({room_rent_limit['value']}% of sum insured); "
                        f"a proportionate deduction applies to associated charges."
                    ),
                }
            )
        else:
            findings.append(
                {
                    "check": "room_rent_sub_limit",
                    "status": "pass",
                    "detail": f"Room rent {room_rent_per_day}/day is within the allowed {allowed:.2f}/day.",
                }
            )


def _check_initial_waiting_period(
    claim: dict, fields: dict, findings: list[dict]
) -> None:
    """Checks whether the claim falls within the policy's initial waiting period."""
    waiting_periods = fields.get("waiting_periods") or {}
    initial_days = waiting_periods.get("initial_days")
    days_since_inception = claim.get("days_since_policy_inception")

    if initial_days is None or days_since_inception is None:
        return

    if days_since_inception < initial_days:
        findings.append(
            {
                "check": "initial_waiting_period",
                "status": "fail",
                "detail": (
                    f"Claim filed {days_since_inception} days after policy inception; "
                    f"initial waiting period is {initial_days} days."
                ),
            }
        )
    else:
        findings.append(
            {
                "check": "initial_waiting_period",
                "status": "pass",
                "detail": "Initial waiting period has been satisfied.",
            }
        )


def _check_procedure_sub_limits(
    claim: dict, fields: dict, findings: list[dict]
) -> None:
    """Checks the claimed procedure against any fixed-amount sub-limits for that category."""
    procedure = (claim.get("procedure") or "").lower()
    billed = claim.get("billed_amount")

    for sub_limit in fields.get("sub_limits") or []:
        category = (sub_limit.get("procedure_or_category") or "").lower()

        if not category or category not in procedure:
            continue

        if sub_limit.get("limit_type") == "fixed_amount" and billed is not None:
            limit_value = sub_limit.get("value")
            if limit_value is not None and billed > limit_value:
                findings.append(
                    {
                        "check": f"sub_limit_{category.replace(' ', '_')}",
                        "status": "fail",
                        "detail": f"Billed amount {billed} exceeds the {limit_value} sub-limit for {category}.",
                    }
                )


# ---------------------------------------------------------------------------
# Node 3
# ---------------------------------------------------------------------------
def retrieve_clauses_for_claim(state: AuditState) -> AuditState:
    """
    Builds a semantic query from the claim's diagnosis/procedure/treatment
    type and retrieves the most relevant clauses for THIS policy_id only.

    Restricting to section_types likely to affect coverage decisions
    (exclusion, condition, inclusion, definition) keeps the result set small
    and focused for the next node.
    """
    claim = state["claim"]
    query = (
        f"Coverage and exclusions related to: {claim.get('diagnosis', '')}, "
        f"procedure: {claim.get('procedure', '')}, "
        f"treatment type: {claim.get('treatment_type', '')}"
    )

    with get_session() as session:
        clauses = retrieve_relevant_clauses(
            session,
            policy_id=state["policy_id"],
            query_text=query,
            section_types=["exclusion", "condition", "inclusion", "definition"],
        )

    state["retrieved_clauses"] = clauses
    return state


# ---------------------------------------------------------------------------
# Node 4
# ---------------------------------------------------------------------------
AUDIT_SYSTEM_PROMPT = """You are a medical insurance claim auditor. You are given:
1. Claim details (diagnosis, procedure, dates, amounts).
2. A set of policy clauses retrieved from the applicable policy wording, each labelled
   with a clause number and section type.

Deterministic numeric checks (sum insured, sub-limits, waiting periods, copay amounts)
have ALREADY been evaluated separately -- do not repeat them. Focus only on whether any
retrieved clause's WORDING excludes, restricts, or imposes a condition or documentation
requirement on this claim.

For each clause that is relevant to the decision, output one finding referencing its
clause number. If none of the retrieved clauses are relevant, return an empty list.

Respond ONLY with JSON of this exact shape:
{"findings": [{"clause_number": "<string>", "status": "pass|fail|flag",
                "reason": "<concise explanation tied to the clause text and claim facts>"}]}"""


def run_llm_clause_audit(state: AuditState) -> AuditState:
    """
    The only node that uses the LLM for interpretation (vs. extraction at
    ingestion time). Receives the claim facts plus the small set of
    retrieved clauses (each with a clause number) and asks the model to
    flag any textual exclusion/condition issue, citing the clause number.

    Because retrieval already narrowed the context to ~5-10 relevant
    clauses for this specific policy, the model's findings can be checked
    against the DB by clause_number -- this is what keeps the output
    auditable rather than a black-box answer over the full document.
    """
    claim = state["claim"]
    clauses = state["retrieved_clauses"] or []

    if not clauses:
        state["llm_findings"] = []
        return state

    clause_block = "\n\n".join(
        f"[Clause {clause['clause_number']}] ({clause['section_type']}) {clause['heading'] or ''}\n{clause['text']}"
        for clause in clauses
    )

    user_prompt = (
        f"Claim details:\n{claim}\n\nRetrieved policy clauses:\n{clause_block}"
    )

    result = call_claude_json(AUDIT_SYSTEM_PROMPT, user_prompt, max_tokens=1500)
    state["llm_findings"] = result.get("findings", [])
    return state


# ---------------------------------------------------------------------------
# Node 5
# ---------------------------------------------------------------------------
def compile_audit_report(state: AuditState) -> AuditState:
    """
    Merges deterministic_findings and llm_findings into one report with an
    overall verdict:

      - any finding with status "fail"  -> overall "rejected"
      - else any finding with "flag"    -> overall "manual_review"
      - else                              -> "approved"

    This is the object returned to the calling application (API response,
    case-management dashboard, etc.) -- every individual finding keeps its
    own `detail`/`reason` and (for clause-based findings) `clause_number`,
    so a human reviewer can trace each part of the decision.
    """
    deterministic = state.get("deterministic_findings") or []
    llm_findings = state.get("llm_findings") or []
    all_findings = deterministic + llm_findings

    if any(f["status"] == "fail" for f in all_findings):
        overall = "rejected"
    elif any(f["status"] == "flag" for f in all_findings):
        overall = "manual_review"
    else:
        overall = "approved"

    state["report"] = {
        "policy_id": state["policy_id"],
        "overall_status": overall,
        "deterministic_findings": deterministic,
        "clause_based_findings": llm_findings,
    }
    return state


# ---------------------------------------------------------------------------
# Graph assembly
# ---------------------------------------------------------------------------
def build_audit_graph():
    """
    Wires the five nodes into a linear LangGraph pipeline and compiles it.

    Why LangGraph rather than a plain function chain: as audit logic grows --
    e.g. adding a "resolve policy_id from claim documents" node up front,
    conditional branches per claim type (inpatient vs. day-care vs.
    maternity), retry/fallback on the LLM node, or a human-in-the-loop
    approval step before `compile_audit_report` -- LangGraph gives you that
    structure (and observability/checkpointing if needed) without rewriting
    the orchestration.

    Build once (e.g. at app startup) and reuse the compiled graph across
    requests.
    """
    graph = StateGraph(AuditState)

    graph.add_node("load_policy_context", load_policy_context)
    graph.add_node("run_deterministic_checks", run_deterministic_checks)
    graph.add_node("retrieve_clauses_for_claim", retrieve_clauses_for_claim)
    graph.add_node("run_llm_clause_audit", run_llm_clause_audit)
    graph.add_node("compile_audit_report", compile_audit_report)

    graph.set_entry_point("load_policy_context")
    graph.add_edge("load_policy_context", "run_deterministic_checks")
    graph.add_edge("run_deterministic_checks", "retrieve_clauses_for_claim")
    graph.add_edge("retrieve_clauses_for_claim", "run_llm_clause_audit")
    graph.add_edge("run_llm_clause_audit", "compile_audit_report")
    graph.add_edge("compile_audit_report", END)

    return graph.compile()


def run_audit(claim: dict, policy_id: int) -> dict:
    """
    Convenience entry point: builds the graph and runs it for one claim.

    In a real service, call build_audit_graph() once at startup and reuse
    the compiled app across requests instead of rebuilding it per call.
    """
    app = build_audit_graph()

    initial_state: AuditState = {
        "claim": claim,
        "policy_id": policy_id,
        "structured_fields": None,
        "retrieved_clauses": None,
        "deterministic_findings": None,
        "llm_findings": None,
        "report": None,
    }

    final_state = app.invoke(initial_state)
    return final_state["report"]
