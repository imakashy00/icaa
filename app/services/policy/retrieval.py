"""
Audit-time data access:

- get_structured_fields()      -> deterministic numbers/rules for a policy (DB read, no LLM)
- retrieve_relevant_clauses()   -> vector search for free-text clauses, scoped to one policy_id

Every retrieval call is scoped to a single policy_id. This is what lets the
same DB hold many companies' many policies without audits ever "seeing" the
wrong policy's wording -- and without per-company query logic.
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.settings import settings
from embeddings import EmbeddingService
from app.models.claim import PolicyClause, PolicyStructuredField, SectionType


def get_structured_fields(session: Session, policy_id: UUID) -> dict | None:
    """
    Fetches the pre-extracted structured fields (sum insured, sub-limits,
    waiting periods, copay, permanent exclusions) for a policy. Cheap DB
    read -- this is the data source for deterministic audit checks, and it
    requires no LLM call at audit time.

    Returns None if the policy hasn't been ingested (or ingestion failed
    before the structured-fields step) -- callers should treat that as a
    hard error, not silently proceed.
    """
    row = (
        session.query(PolicyStructuredField)
        .filter(PolicyStructuredField.policy_id == policy_id)
        .first()
    )
    if row is None:
        return None

    return {
        "sum_insured": float(row.sum_insured) if row.sum_insured is not None else None,
        "room_rent_limit": row.room_rent_limit,
        "copay": row.copay,
        "waiting_periods": row.waiting_periods,
        "sub_limits": row.sub_limits,
        "permanent_exclusions": row.permanent_exclusions,
    }


def retrieve_relevant_clauses(
    session: Session,
    policy_id: UUID,
    query_text: str,
    top_k: int = settings.top_k_clauses,
    section_types: list[str] | None = None,
) -> list[dict]:
    """
    Embeds `query_text` and runs a pgvector cosine-similarity search scoped
    to `policy_id` (and optionally to specific `section_types`, e.g. only
    "exclusion" and "condition" clauses when checking whether a procedure is
    covered).

    `query_text` is typically built from the claim's diagnosis/procedure plus
    a short description of what's being checked -- see
    retrieve_clauses_for_claim() in audit_graph.py.

    Returns the matched clauses with enough metadata (clause_number, heading,
    page, section_type) for the audit LLM step to cite them, and for a human
    reviewer to verify against the source PDF.
    """
    embedder = EmbeddingService()
    query_embedding = embedder.embed_query(query_text)

    stmt = (
        select(PolicyClause)
        .where(PolicyClause.policy_id == policy_id)
        .order_by(PolicyClause.embedding.cosine_distance(query_embedding))
        .limit(top_k)
    )

    if section_types:
        stmt = stmt.where(
            PolicyClause.section_type.in_([SectionType(s) for s in section_types])
        )

    results = session.execute(stmt).scalars().all()

    return [
        {
            "clause_number": clause.clause_number,
            "heading": clause.heading,
            "text": clause.clause_text,
            "page": clause.page_number,
            "section_type": clause.section_type.value,
        }
        for clause in results
    ]
