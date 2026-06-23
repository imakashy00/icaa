"""
End-to-end ingestion: PDF in, fully populated Policy/PolicyClause/
PolicyStructuredField rows out. This is the single function you call once
per policy document (and again per renewal/version).
"""
import os
import datetime

from sqlalchemy.orm import Session

from app.services.policy.embeddings import EmbeddingService
from app.models.claim import Policy, PolicyClause, PolicyStructuredField, SectionType
from app.services.policy.chunker import chunk_policy_pages
from app.services.policy.extractor import classify_clauses, extract_structured_fields
from app.services.policy.parser import parse_policy_pdf


def ingest_policy_document(
    # session: Session,
    file_path: str,
    company_id: int,
    policy_name: str,
    policy_code: str,
    version: str = "v1",
):
    """
    Full ingestion pipeline for one policy PDF:

      1. parse_policy_pdf          -- PDF -> per-page markdown (pymupdf4llm)
      2. chunk_policy_pages         -- markdown -> clause-level chunks
      3. classify_clauses           -- LLM tags each chunk's section_type
      4. EmbeddingService            -- embeds every chunk
      5. extract_structured_fields   -- LLM pulls sum insured / sub-limits /
                                         copay / waiting periods / exclusions
      6. persist Policy, PolicyClause rows (with embeddings), and
         PolicyStructuredField

    Returns the new policy_id.
    """
    pages = parse_policy_pdf(file_path)
    chunks = chunk_policy_pages(pages)
    chunks = classify_clauses(chunks)

    embedder = EmbeddingService()
    texts = [c["text"] for c in chunks]
    embeddings = embedder.embed_texts(texts)

    full_text = "\n\n".join(texts)
    structured = extract_structured_fields(full_text)
    print(structured)
    print(full_text)
    policy = Policy(
        company_id=company_id,
        policy_name=policy_name,
        policy_code=policy_code,
        version=version,
        source_file=file_path,
        ingested_at=datetime.datetime.now(),
    )
    # session.add(policy)
    # session.flush()  # assigns policy.id without committing the transaction

    for chunk, embedding in zip(chunks, embeddings):
        # session.add(
        #     PolicyClause(
        #         policy_id=policy.id,
        #         clause_number=chunk["clause_number"],
        #         heading=chunk["heading"],
        #         clause_text=chunk["text"],
        #         section_type=SectionType(chunk["section_type"]),
        #         page_number=chunk["page"],
        #         embedding=embedding,
        #     )
        # )
        print(PolicyClause(
                policy_id=policy.id,
                clause_number=chunk["clause_number"],
                heading=chunk["heading"],
                clause_text=chunk["text"],
                section_type=SectionType(chunk["section_type"]),
                page_number=chunk["page"],
                embedding=embedding,
            ))

    # session.add(
    #     PolicyStructuredField(
    #         policy_id=policy.id,
    #         sum_insured=_first_or_none(structured.get("sum_insured_options")),
    #         room_rent_limit=structured.get("room_rent_limit"),
    #         copay=structured.get("copay"),
    #         waiting_periods=structured.get("waiting_periods"),
    #         sub_limits=structured.get("sub_limits"),
    #         permanent_exclusions=structured.get("permanent_exclusions"),
    #         raw_extraction=structured,
    #     )
    # )
    print(
        PolicyStructuredField(
            policy_id=policy.id,
            sum_insured=_first_or_none(structured.get("sum_insured_options")),
            room_rent_limit=structured.get("room_rent_limit"),
            copay=structured.get("copay"),
            waiting_periods=structured.get("waiting_periods"),
            sub_limits=structured.get("sub_limits"),
            permanent_exclusions=structured.get("permanent_exclusions"),
            raw_extraction=structured,
        )
    )

    return policy.id


def _first_or_none(values):
    """Helper: picks the first sum-insured option as the default; full list stays in raw_extraction."""
    return values[0] if values else None


if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # Safely joins it with your PDF filename
    pdf_path = os.path.join(current_dir, "policy.pdf")
    ingest_policy_document(pdf_path, 89, 'health policy', 'sjfsfo309w', 'v1')
