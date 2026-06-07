from __future__ import annotations

import operator
from typing import Annotated, Any, Dict, List, Optional, TypedDict


class ClaimState(TypedDict, total=False):
    # Documents
    claim_form: Dict[str, Any]
    other_docs: Optional[List[str]]
    document_texts: Dict[str, str]
    classified_documents: Dict[str, Dict[str, Any]]
    extracted_documents: Dict[str, Dict[str, Any]]

    # Raw Inputs
    claim_id: str
    uploaded_files: List[str]
    raw_text: str
    ocr_completed: str

    # Insured Policy Details
    policy_no: Optional[str]
    company_tpa_id: Optional[str]
    insured_name: Optional[str]
    insured: Optional[str]
    phone: Optional[str]
    email: Optional[str]

    # Patient Details
    patient_name: Optional[str]
    relationship_to_insured: Optional[str]
    gender: Optional[str]
    occupation: Optional[str]
    patient_age: Optional[int]
    patient_dob: Optional[str]

    # Hospitalization Details
    hospital_name: Optional[str]
    hospital_type: Optional[str]
    room_category: Optional[str]
    hospitalization_reason: Optional[str]
    diagnosis: Optional[str]
    primary_icd_code: Optional[str]
    admission_date: Optional[str]
    discharge_date: Optional[str]
    injury_case: Optional[bool]
    medico_legal_case: Optional[bool]
    police_reported: Optional[bool]

    # Claim Details
    hospitalization_expenses: Optional[float]
    pre_hospitalization_expenses: Optional[float]
    post_hospitalization_expenses: Optional[float]
    ambulance_charges: Optional[float]
    total_claim_amount: float

    # Document Validation
    submitted_docs: List[str]
    missing_docs: List[str]
    document_validation_status: Optional[str]

    # Extraction Confidence
    extraction_confidence: float
    extraction_errors: List[str]

    # Bank Details
    bank_account_no: Optional[str]
    ifsc_or_routing_code: Optional[str]
    pan_or_tax_id: Optional[str]

    # Evidence / Verification
    evidence_bundle: Dict[str, Any]
    verification_results: Dict[str, Any]
    identity_verified: bool
    policy_verified: bool
    hospital_verified: bool
    medical_verified: bool
    bank_verified: bool

    # Fraud Details
    fraud_score: float
    fraud_flags: Annotated[List[str], operator.add]
    fraud_deduction_pct: float
    duplicate_claim_detected: bool
    suspicious_patterns: List[str]

    # Policy Eligibility
    policy_active: bool
    coverage_eligible: bool
    waiting_period_completed: bool
    exclusions_found: List[str]
    approved_coverage_amount: Optional[float]
    policy_analysis: Dict[str, Any]

    # Human Review
    final_decision: Optional[str]
    rejection_reason: Optional[str]
    approved_amount: Optional[float]
    final_report: Dict[str, Any]
    audit_summary: Dict[str, Any]

    # Workflow Control
    current_agent: str
    next_step: str
    workflow_history: List[str]
