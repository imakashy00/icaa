from __future__ import annotations

import operator
from typing import Annotated, Any, Dict, List, Optional, TypedDict

from dotenv import load_dotenv
from langgraph.graph import END, START, StateGraph

from app.layers.audit import audit_node
from app.layers.decision import decision_node
from app.layers.evidence_aggregation import evidence_node
from app.layers.fraud_analysis import analyze_fraud
from app.layers.policy_analysis import policy_analysis_node
from app.layers.verification import verification_node
from app.nodes.aggregation import claim_aggregation_node
from app.nodes.classification import document_classifier_node
from app.nodes.extraction import extraction_node

load_dotenv()


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


def _route_next_step(state: ClaimState) -> str:
    return state.get("next_step", "completed")


workflow = StateGraph(ClaimState)

workflow.add_node("document_classifier", document_classifier_node)
workflow.add_node("document_extraction", extraction_node)
workflow.add_node("claim_aggregation", claim_aggregation_node)
workflow.add_node("evidence_aggregation", evidence_node)
workflow.add_node("verification", verification_node)
workflow.add_node("policy_analysis", policy_analysis_node)
workflow.add_node("fraud_analysis", analyze_fraud)
workflow.add_node("decision", decision_node)
workflow.add_node("audit", audit_node)

workflow.add_edge(START, "document_classifier")
workflow.add_conditional_edges(
    "document_classifier",
    _route_next_step,
    {
        "document_extraction": "document_extraction",
        "completed": END,
    },
)
workflow.add_conditional_edges(
    "document_extraction",
    _route_next_step,
    {
        "claim_aggregation": "claim_aggregation",
        "completed": END,
    },
)
workflow.add_conditional_edges(
    "claim_aggregation",
    _route_next_step,
    {
        "evidence_aggregation": "evidence_aggregation",
        "completed": END,
    },
)
workflow.add_conditional_edges(
    "evidence_aggregation",
    _route_next_step,
    {
        "verification": "verification",
        "completed": END,
    },
)
workflow.add_conditional_edges(
    "verification",
    _route_next_step,
    {
        "policy_analysis": "policy_analysis",
        "completed": END,
    },
)
workflow.add_conditional_edges(
    "policy_analysis",
    _route_next_step,
    {
        "fraud_analysis": "fraud_analysis",
        "completed": END,
    },
)
workflow.add_conditional_edges(
    "fraud_analysis",
    _route_next_step,
    {
        "decision": "decision",
        "completed": END,
    },
)
workflow.add_conditional_edges(
    "decision",
    _route_next_step,
    {
        "audit": "audit",
        "completed": END,
    },
)
workflow.add_conditional_edges(
    "audit",
    _route_next_step,
    {
        "completed": END,
    },
)

app = workflow.compile()




