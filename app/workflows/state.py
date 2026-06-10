from __future__ import annotations

import operator
from openai import BaseModel
from typing import Annotated, Any, Dict, List, Optional
from app.schemas.claim_form import BankDetails, BenefitDetails, ClaimExpenses, DocumentChecklist, HospitalDetails, InsuranceHistory, PatientDetails, PolicyRecord, PrescriptionRecord, PrimaryInsured


class ClaimState(BaseModel):
    primary_insured: PrimaryInsured
    insurance_history: InsuranceHistory
    patient_details:PatientDetails
    prescriptions:PrescriptionRecord
    hospital_details:HospitalDetails
    bank_details: BankDetails
    claim_details:ClaimExpenses
    benefit_details:BenefitDetails
    docs_checklist:DocumentChecklist
    policy_record:PolicyRecord

    # Fraud Details
    fraud_score: float
    fraud_flags: Annotated[List[str], operator.add]

    # Human Review
    final_decision: Optional[str]
    rejection_reason: Optional[str]
    approved_amount: Optional[float]
    final_report: Dict[str, Any]
    audit_summary: Dict[str, Any]

    # Workflow Control
    current_agent: Optional[str]
    next_step: Optional[str]
    workflow_history: List[str]
