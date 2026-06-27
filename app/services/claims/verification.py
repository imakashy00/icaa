from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session
from datetime import date


from app.core.db import SessionLocal
from app.workflows.state import ClaimState


from app.models.claim import PolicyContract, PolicyMember


def verify_user(
    state: ClaimState,
    db: Session,
):
    policy = db.scalar(
        select(PolicyContract).where(PolicyContract.policy_no == state.primary_insured.policy_no)
    )

    if not policy:
        state.verification.user.passed = False
        state.verification.user.reason = "PolicyContract number not found"
        return

    if (
        policy.policy_holder_name.lower().strip()
        != state.primary_insured.policy_holder_name.lower().strip()
    ):
        state.verification.user.passed = False
        state.verification.user.reason = "PolicyContract holder name mismatch"
        return

    state.verification.user.passed = True



def verify_insurance(
    state: ClaimState,
    db: Session,
):
    policy = db.scalar(
        select(PolicyContract).where(PolicyContract.policy_no == state.primary_insured.policy_no)
    )

    if not policy:
        state.verification.policy.passed = False
        state.verification.policy.reason = "PolicyContract not found"
        return

    today = date.today()

    if not policy.active:
        state.verification.policy.passed = False
        state.verification.policy.reason = "PolicyContract inactive"
        return

    if policy.start_date > today:
        state.verification.policy.passed = False
        state.verification.policy.reason = "PolicyContract not started"
        return

    if policy.end_date < today:
        state.verification.policy.passed = False
        state.verification.policy.reason = "PolicyContract expired"
        return

    if policy.available_sum_insured <= 0:
        state.verification.policy.passed = False
        state.verification.policy.reason = "No remaining coverage"
        return

    state.verification.policy.passed = True


def verify_patient_details(
    state: ClaimState,
    db: Session,
):
    policy = db.scalar(
        select(PolicyContract).where(PolicyContract.policy_no == state.primary_insured.policy_no)
    )

    if not policy:
        state.verification.patient.passed = False
        state.verification.patient.reason = "PolicyContract not found"
        return

    beneficiary = db.scalar(
        select(PolicyMember).where(
            PolicyMember.policy_id == policy.id,
            PolicyMember.name == state.patient_details.patient_name,
        )
    )

    if not beneficiary:
        state.verification.patient.passed = False
        state.verification.patient.reason = "Patient not covered under policy"
        return

    relation = beneficiary.relationship_to_holder.lower()

    claim_relation = state.patient_details.relationship_to_policy_holder.lower()

    if relation != claim_relation:
        state.verification.patient.passed = False
        state.verification.patient.reason = "Relationship mismatch"
        return

    state.verification.patient.passed = True


def compute_verification_status(
    state: ClaimState,
):
    checks = [
        state.verification.user.passed,
        state.verification.policy.passed,
        state.verification.patient.passed,
        state.verification.documents.passed,
    ]

    state.verification.overall_verified = all(checks)



async def verification_node(state: ClaimState):
    print("Verifying data...")

    with SessionLocal() as db:
        verify_user(state, db)
        verify_insurance(state, db)
        verify_patient_details(state, db)

    compute_verification_status(state)

    if not state.verification.overall_verified:
        return {
            "verification": state.verification,
            "next_step": "completed",
        }

    return {
        "verification": state.verification,
        "next_step": "policy_analysis",
    }
