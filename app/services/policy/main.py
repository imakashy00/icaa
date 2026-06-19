"""
Example usage:

    1. init_db()                                -- one-time schema setup
    2. ingest_policy_document(...)              -- once per policy PDF
    3. run_audit(claim, policy_id)               -- once per claim

Run with: python main.py
(requires DATABASE_URL and ANTHROPIC_API_KEY env vars, and a real PDF path)
"""

from database import get_session, init_db
from app.models.claim import Company
from app.services.policy.pipeline import ingest_policy_document
from audit_graph import run_audit


def get_or_create_company(session, name: str) -> int:
    """Looks up a company by name, creating it if it doesn't exist yet. Returns its id."""
    company = session.query(Company).filter_by(name=name).first()
    if company is None:
        company = Company(name=name)
        session.add(company)
        session.flush()
    return company.id


if __name__ == "__main__":
    init_db()

    with get_session() as session:
        company_id = get_or_create_company(session, "Acme Health Insurance")

        policy_id = ingest_policy_document(
            session,
            file_path="/path/to/acme_gold_plan_2026.pdf",
            company_id=company_id,
            policy_name="Acme Gold Health Plan",
            policy_code="ACME-GOLD-2026",
        )
        print(f"Ingested policy_id={policy_id}")

    sample_claim = {
        "claim_id": "CLM-1001",
        "diagnosis": "Cataract surgery, left eye",
        "procedure": "Phacoemulsification with IOL implantation",
        "treatment_type": "day_care",
        "billed_amount": 45000,
        "room_rent_per_day": 0,
        "days_since_policy_inception": 420,
    }

    report = run_audit(sample_claim, policy_id=policy_id)
    print(report)
