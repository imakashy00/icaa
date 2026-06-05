from __future__ import annotations

from typing import Any, Dict

from app.graph.orchestrator import ClaimState


AGGREGATION_TARGETS = {
    "ClaimForm": "claim_form",
    "PrimaryInsured": "primary_insured",
    "InsuranceHistory": "insurance_history",
    "PatientDetails": "patient_details",
    "HospitalizationDetails": "hospitalization_details",
    "ClaimExpenses": "claim_expenses",
    "BenefitDetails": "benefits",
    "DocumentChecklist": "document_checklist",
    "HospitalDetails": "hospital_details",
    "DiagnosisAndTreatment": "diagnosis_and_treatment",
    "BankDetails": "bank_details",
    "Declaration": "declaration",
}


def _ensure_dict(value: Any) -> Dict[str, Any]:
    if isinstance(value, dict):
        return value
    if hasattr(value, "model_dump"):
        return value.model_dump()
    return {}


async def claim_aggregation_node(state: ClaimState):
    extracted_documents = state.get("extracted_documents", {})
    claim_form = _ensure_dict(state.get("claim_form", {}))

    for document_name, document_payload in extracted_documents.items():
        document_type = document_payload.get("document_type")
        data = _ensure_dict(document_payload.get("data", {}))

        if document_type == "ClaimForm":
            claim_form.update(data)
            continue

        target_key = AGGREGATION_TARGETS.get(document_type)
        if not target_key:
            continue

        claim_form[target_key] = data

    primary_insured = _ensure_dict(claim_form.get("primary_insured", {}))
    patient_details = _ensure_dict(claim_form.get("patient_details", {}))
    hospitalization_details = _ensure_dict(claim_form.get("hospitalization_details", {}))
    claim_expenses = _ensure_dict(claim_form.get("claim_expenses", {}))
    hospital_details = _ensure_dict(claim_form.get("hospital_details", {}))
    diagnosis_and_treatment = _ensure_dict(claim_form.get("diagnosis_and_treatment", {}))
    bank_details = _ensure_dict(claim_form.get("bank_details", {}))

    diagnosis = _ensure_dict(diagnosis_and_treatment.get("diagnosis", {}))

    total_claim_amount = claim_expenses.get("total_expenses")
    if total_claim_amount is None:
        total_claim_amount = sum(
            float(claim_expenses.get(field) or 0.0)
            for field in (
                "hospitalization_expenses",
                "pre_hospitalization_expenses",
                "post_hospitalization_expenses",
                "ambulance_charges",
                "health_checkup_cost",
                "other_expenses",
            )
        )

    workflow_history = list(state.get("workflow_history", []))
    workflow_history.append("ClaimAggregationAgent: merged extracted document payloads into canonical claim form")

    return {
        "claim_form": claim_form,
        "policy_no": primary_insured.get("policy_no") or state.get("policy_no"),
        "company_tpa_id": primary_insured.get("tpa_id") or state.get("company_tpa_id"),
        "insured_name": primary_insured.get("policy_holder_name") or state.get("insured_name"),
        "patient_name": patient_details.get("patient_name") or state.get("patient_name"),
        "relationship_to_insured": patient_details.get("relationship_to_policy_holder") or state.get("relationship_to_insured"),
        "patient_age": patient_details.get("age") or state.get("patient_age"),
        "patient_dob": patient_details.get("date_of_birth") or state.get("patient_dob"),
        "room_category": patient_details.get("room_category") or state.get("room_category"),
        "hospitalization_reason": patient_details.get("hospitalization_reason") or state.get("hospitalization_reason"),
        "hospital_name": hospital_details.get("hospital_name") or state.get("hospital_name"),
        "hospital_type": hospital_details.get("hospital_type") or state.get("hospital_type"),
        "diagnosis": hospital_details.get("diagnosis") or diagnosis.get("primary_icd_description") or state.get("diagnosis"),
        "primary_icd_code": diagnosis.get("primary_icd_code") or state.get("primary_icd_code"),
        "admission_date": hospitalization_details.get("date_of_admission") or state.get("admission_date"),
        "discharge_date": hospitalization_details.get("date_of_discharge") or state.get("discharge_date"),
        "hospitalization_expenses": claim_expenses.get("hospitalization_expenses") or state.get("hospitalization_expenses"),
        "pre_hospitalization_expenses": claim_expenses.get("pre_hospitalization_expenses") or state.get("pre_hospitalization_expenses"),
        "post_hospitalization_expenses": claim_expenses.get("post_hospitalization_expenses") or state.get("post_hospitalization_expenses"),
        "ambulance_charges": claim_expenses.get("ambulance_charges") or state.get("ambulance_charges"),
        "total_claim_amount": total_claim_amount or state.get("total_claim_amount", 0.0),
        "bank_account_no": bank_details.get("account_no") or state.get("bank_account_no"),
        "ifsc_or_routing_code": bank_details.get("ifsc") or state.get("ifsc_or_routing_code"),
        "extraction_confidence": max(0.5, 1.0 - (len(state.get("extraction_errors", [])) * 0.05)),
        "workflow_history": workflow_history,
        "current_agent": "ClaimAggregationAgent",
        "next_step": "evidence_aggregation",
    }
