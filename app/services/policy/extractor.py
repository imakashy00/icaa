"""
LLM-based steps run ONCE per policy at ingestion time:

1. classify_clauses()           -> tags each clause chunk with a section_type
2. extract_structured_fields()  -> pulls sum insured, sub-limits, copay,
                                    waiting periods, exclusions into fixed JSON

Both results are persisted (PolicyClause.section_type, PolicyStructuredField),
so audit-time code never needs to re-classify or re-extract -- it only reads
from the DB and runs a much smaller, targeted LLM call (see audit_graph.py).
"""

from app.models.claim import SectionType
from llm_client import call_claude_json

_VALID_SECTION_TYPES = {member.value for member in SectionType}


CLASSIFY_SYSTEM_PROMPT = """You are an insurance policy analyst. You will be given a numbered
list of clause excerpts from a health insurance policy document. For each clause, classify it
into exactly one of these categories:
definition, exclusion, inclusion, waiting_period, sub_limit, copay, condition, claim_procedure, general

Respond ONLY with a JSON object of this exact shape, with one entry per clause in the same order:
{"classifications": ["<category>", "<category>", ...]}"""


def classify_clauses(chunks: list[dict], batch_size: int = 15) -> list[dict]:
    """
    Tags each clause chunk with a `section_type` via the LLM, in batches to
    keep prompts small and cheap. Mutates and returns `chunks` with an added
    "section_type" key (falling back to "general" if the model returns an
    invalid or missing label, so ingestion never fails outright due to a
    classification glitch).

    Why batched and done once: this is the only place an LLM "looks at" the
    whole document, and it happens a single time per policy version --
    not on every claim.
    """
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i : i + batch_size]

        clause_list = "\n\n".join(
            f"Clause {j + 1}: [{c['clause_number'] or 'N/A'}] {c['heading'] or ''}\n{c['text'][:600]}"
            for j, c in enumerate(batch)
        )

        result = call_claude_json(CLASSIFY_SYSTEM_PROMPT, clause_list, max_tokens=500)
        labels = result.get("classifications", [])

        for c, label in zip(batch, labels):
            c["section_type"] = label if label in _VALID_SECTION_TYPES else "general"

        # If the model returned fewer labels than clauses in the batch
        for c in batch[len(labels) :]:
            c["section_type"] = "general"

    return chunks


EXTRACT_FIELDS_SYSTEM_PROMPT = """You are an insurance policy analyst. You will be given the
full text of a health insurance policy wording document (concatenated clauses).
Extract the following fields as JSON. If a field is not explicitly stated in the text,
use null -- do not guess or infer values that are not written.

{
  "sum_insured_options": [<numbers, in policy currency, or empty list>],
  "room_rent_limit": {"type": "percentage_of_si | fixed_amount | no_limit | single_private_ac | other",
                       "value": <number or null>},
  "copay": [{"condition": "<e.g. age above 60, all claims>", "percentage": <number>}],
  "waiting_periods": {"initial_days": <int|null>,
                       "pre_existing_disease_months": <int|null>,
                       "specific_disease_months": <int|null>,
                       "maternity_months": <int|null>},
  "sub_limits": [{"procedure_or_category": "<name>",
                   "limit_type": "percentage_of_si|fixed_amount",
                   "value": <number>}],
  "permanent_exclusions": ["<short description>", ...]
}

Respond ONLY with this JSON object, no commentary, no markdown fences."""


def extract_structured_fields(full_policy_text: str) -> dict:
    """
    Runs a single LLM pass over the policy text to extract the numeric/rule
    fields the audit pipeline needs for deterministic checks: sum insured,
    sub-limits, copay percentages, waiting periods, and permanent exclusions.

    Why this matters: deterministic checks (sum insured sufficiency, sub-limit
    breaches, waiting period elapsed) drive pass/fail audit outcomes and must
    be reproducible. Asking an LLM to re-derive these numbers at audit time
    from raw text is a hallucination risk; extracting them once into a fixed
    JSON shape -- reviewable by a human before go-live -- makes them a stable,
    queryable part of the schema instead.

    Input is truncated to stay comfortably within context limits. For very
    large/complex policies, consider extracting per `section_type` (e.g. feed
    only the "sub_limit"-tagged clauses for the sub_limits field) instead of
    one pass over the whole document.
    """
    truncated = full_policy_text[:60000]
    return call_claude_json(EXTRACT_FIELDS_SYSTEM_PROMPT, truncated, max_tokens=2000)
