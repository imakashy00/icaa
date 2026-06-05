from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional


def _parse_date(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None

    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    return None


def _claims_to_dicts(claim_history: Any) -> List[Dict[str, Any]]:
    if not claim_history:
        return []

    normalized: List[Dict[str, Any]] = []
    for item in claim_history:
        if isinstance(item, dict):
            normalized.append(item)
        elif hasattr(item, "model_dump"):
            normalized.append(item.model_dump())
    return normalized


def analyze_fraud(state: Any) -> Dict[str, Any]:
    evidence_bundle = state.get("evidence_bundle", {})
    claim_history = _claims_to_dicts(evidence_bundle.get("claim_history"))
    current_claim_id = evidence_bundle.get("claim_id") or state.get("claim_id")
    claim_form = state.get("claim_form") or {}
    hospital_details = (
        claim_form.get("hospital_details") if isinstance(claim_form, dict) else {}
    )
    claim_expenses = (
        claim_form.get("claim_expenses") if isinstance(claim_form, dict) else {}
    )
    diagnosis_and_treatment = (
        claim_form.get("diagnosis_and_treatment")
        if isinstance(claim_form, dict)
        else {}
    )
    diagnosis = (
        diagnosis_and_treatment.get("diagnosis")
        if isinstance(diagnosis_and_treatment, dict)
        else {}
    )
    procedures = (
        diagnosis_and_treatment.get("procedures")
        if isinstance(diagnosis_and_treatment, dict)
        else []
    )

    prior_bill_numbers = set()
    for prior_claim in claim_history:
        if prior_claim.get("claim_id") == current_claim_id:
            continue
        for bill in prior_claim.get("bills_details", []) or []:
            bill_no = bill.get("bill_no") if isinstance(bill, dict) else None
            if bill_no:
                prior_bill_numbers.add(str(bill_no).strip().casefold())

    fraud_flags: List[str] = []
    suspicious_patterns: List[str] = []
    fraud_score = 0.0

    if not evidence_bundle.get("policy_active", False):
        fraud_flags.append("Policy is inactive or not found in evidence.")
        fraud_score += 25.0

    if not state.get("identity_verified", False):
        fraud_flags.append("Identity verification failed.")
        fraud_score += 15.0

    if not state.get("hospital_verified", False):
        fraud_flags.append("Hospital verification failed.")
        fraud_score += 10.0

    claimed_amount = float(
        (claim_expenses or {}).get("total_expenses")
        or state.get("total_claim_amount")
        or 0.0
    )
    if claimed_amount <= 0:
        fraud_flags.append("Claimed amount is missing or zero.")
        fraud_score += 10.0

    duplicate_detected = False
    admission_date = _parse_date(state.get("admission_date"))
    hospital_name = state.get("hospital_name") or (hospital_details or {}).get(
        "hospital_name"
    )
    for prior_claim in claim_history:
        if prior_claim.get("claim_id") == current_claim_id:
            continue

        prior_claim_form = prior_claim.get("claim_form", {})
        prior_hospital = (
            prior_claim_form.get("hospital_details", {})
            if isinstance(prior_claim_form, dict)
            else {}
        )
        prior_expenses = (
            prior_claim_form.get("claim_expenses", {})
            if isinstance(prior_claim_form, dict)
            else {}
        )
        prior_diagnosis_and_treatment = (
            prior_claim_form.get("diagnosis_and_treatment", {})
            if isinstance(prior_claim_form, dict)
            else {}
        )
        prior_diagnosis = (
            prior_diagnosis_and_treatment.get("diagnosis", {})
            if isinstance(prior_diagnosis_and_treatment, dict)
            else {}
        )
        prior_procedures = (
            prior_diagnosis_and_treatment.get("procedures", [])
            if isinstance(prior_diagnosis_and_treatment, dict)
            else []
        )
        prior_admission = None
        if isinstance(prior_claim_form, dict):
            hospitalization_details = prior_claim_form.get(
                "hospitalization_details", {}
            )
            if isinstance(hospitalization_details, dict):
                prior_admission = _parse_date(
                    hospitalization_details.get("date_of_admission")
                )

        prior_amount = float((prior_expenses or {}).get("total_expenses") or 0.0)
        same_hospital = bool(
            hospital_name and hospital_name == prior_hospital.get("hospital_name")
        )
        same_amount = prior_amount > 0 and abs(prior_amount - claimed_amount) <= max(
            500.0, prior_amount * 0.05
        )
        close_in_time = bool(
            admission_date
            and prior_admission
            and abs((admission_date - prior_admission).days) <= 30
        )
        same_diagnosis = bool(
            diagnosis
            and prior_diagnosis
            and diagnosis.get("primary_icd_code")
            and diagnosis.get("primary_icd_code")
            == prior_diagnosis.get("primary_icd_code")
        )
        same_procedure = bool(
            procedures
            and prior_procedures
            and any(
                (procedure or {}).get("code")
                and any(
                    (prior_procedure or {}).get("code") == (procedure or {}).get("code")
                    for prior_procedure in prior_procedures
                )
                for procedure in procedures
            )
        )
        same_bill_number = any(
            str((bill or {}).get("bill_no", "")).strip().casefold()
            in prior_bill_numbers
            for bill in (state.get("bills_details") or [])
            if isinstance(bill, dict)
        )

        if (
            same_hospital
            and same_amount
            and close_in_time
            and (same_diagnosis or same_procedure)
        ) or same_bill_number:
            duplicate_detected = True
            fraud_flags.append(
                "Possible duplicate claim matches a prior claim record by bill number or claim pattern."
            )
            fraud_score += 35.0
            break

    prior_claim_count = sum(
        1 for item in claim_history if item.get("claim_id") != current_claim_id
    )
    if prior_claim_count >= 2:
        suspicious_patterns.append("Multiple prior claims found for the same policy.")
        fraud_score += 5.0

    if evidence_bundle.get("hospital") and not evidence_bundle["hospital"].get(
        "in_network", True
    ):
        suspicious_patterns.append("Hospital is outside the preferred network.")
        fraud_score += 10.0

    if not state.get("medical_verified", False):
        suspicious_patterns.append("Medical records are incomplete or inconsistent.")
        fraud_score += 5.0

    fraud_score = round(min(fraud_score, 100.0), 2)
    fraud_deduction_pct = 0.0
    if fraud_score >= 50:
        fraud_deduction_pct = 25.0
    elif fraud_score >= 25:
        fraud_deduction_pct = 10.0

    workflow_history = list(state.get("workflow_history", []))
    workflow_history.append(
        "FraudAgent: scored duplicate and anomaly risk from claim history and evidence"
    )

    return {
        "fraud_score": fraud_score,
        "fraud_flags": fraud_flags,
        "duplicate_claim_detected": duplicate_detected,
        "suspicious_patterns": suspicious_patterns,
        "fraud_deduction_pct": fraud_deduction_pct,
        "workflow_history": workflow_history,
        "current_agent": "FraudAgent",
        "next_step": "decision",
    }
