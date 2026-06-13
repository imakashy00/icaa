from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.db import SessionLocal
from app.workflows.state import (
    ClaimState,
    InsuranceHistory,
    PatientDetails,
    PrimaryInsured,
)


def verify_user(user: PrimaryInsured, db: Session):
    pass


def verify_insurance(insurance: InsuranceHistory, db: Session):
    pass


def verify_patient_details(patient_details: PatientDetails, db: Session):
    pass


async def verification_node(state: ClaimState):
    print("Verifying data...")
    # verify user
    with SessionLocal() as db:
        verify_user(state.primary_insured, db=db)
        # verify policy(coverage , start date , end date , amount used )
        verify_insurance(state.insurance_history, db=db)
        # verify users relation to patient
        verify_patient_details(state.patient_details, db=db)
    if not state.verification.overall_verified:
        return {"next_step": "completed"}
    return {"next_step": "policy_analysis"}
