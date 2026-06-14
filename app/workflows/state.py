from __future__ import annotations
from typing import Annotated, Any, Dict, List, Optional
import operator

from pydantic import BaseModel
from app.schemas.claim_form import BankDetails, BenefitDetails, ClaimExpenses, DocumentChecklist, HospitalDetails, HospitalizationDetails, InsuranceHistory, PatientDetails, PolicyRecord, PrescriptionRecord, PrimaryInsured, VerificationResult


class ClaimState(BaseModel):

    document_text:Optional[str] 

    primary_insured: PrimaryInsured
    insurance_history: InsuranceHistory
    patient_details:PatientDetails
    prescriptions: List[PrescriptionRecord]
    hospital_details:HospitalDetails
    hospitalization_details:HospitalizationDetails
    bank_details: BankDetails
    claim_details:ClaimExpenses
    benefit_details:BenefitDetails
    docs_checklist:DocumentChecklist
    policy_record:PolicyRecord
    verification: VerificationResult

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

