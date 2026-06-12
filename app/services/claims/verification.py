from __future__ import annotations

from difflib import SequenceMatcher
from typing import Any, Dict, Mapping, Optional


def _normalize(value: Optional[str]) -> str:
    return (value or "").strip().casefold()


def _similarity(left: Optional[str], right: Optional[str]) -> float:
    if not left or not right:
        return 0.0
    return SequenceMatcher(None, _normalize(left), _normalize(right)).ratio()


def compare_identity(
    extracted_name: Optional[str], evidence_name: Optional[str]
) -> Dict[str, Any]:
    score = _similarity(extracted_name, evidence_name)
    return {
        "match": score >= 0.85,
        "similarity_score": score,
        "reason": None
        if score >= 0.85
        else "Claimant name does not sufficiently match policy holder name.",
    }


def verify_policy(
    policy: Optional[Dict[str, Any]], policy_no: Optional[str]
) -> Dict[str, Any]:
    if not policy:
        return {"match": False, "reason": "Policy record not found."}

    matches_policy_no = policy_no == policy.get("policy_no")
    is_active = bool(policy.get("active"))
    return {
        "match": matches_policy_no and is_active,
        "reason": None
        if matches_policy_no and is_active
        else "Policy number mismatch or policy is inactive.",
        "policy_active": is_active,
    }


def verify_hospital(
    extracted_hospital_name: Optional[str], evidence_hospital: Optional[Dict[str, Any]]
) -> Dict[str, Any]:
    if not evidence_hospital:
        return {"match": False, "reason": "Hospital record not found."}

    score = _similarity(extracted_hospital_name, evidence_hospital.get("hospital_name"))
    in_network = bool(evidence_hospital.get("in_network"))
    return {
        "match": score >= 0.85 and in_network,
        "similarity_score": score,
        "in_network": in_network,
        "reason": None
        if score >= 0.85 and in_network
        else "Hospital does not match or is not in network.",
    }


def verify_medical_data(state: Mapping[str, Any]) -> Dict[str, Any]:
    diagnosis = state.get("diagnosis")
    admission_date = state.get("admission_date")
    discharge_date = state.get("discharge_date")
    claim_form = state.get("claim_form") or {}
    diagnosis_and_treatment = (
        claim_form.get("diagnosis_and_treatment")
        if isinstance(claim_form, dict)
        else None
    )

    has_core_fields = bool(
        diagnosis
        or (diagnosis_and_treatment and diagnosis_and_treatment.get("diagnosis"))
    )
    has_dates = bool(admission_date and discharge_date)

    return {
        "match": has_core_fields and has_dates,
        "reason": None
        if has_core_fields and has_dates
        else "Medical details are incomplete or missing hospitalization dates.",
    }


def verify_bank_details(
    account_no: Optional[str], ifsc: Optional[str]
) -> Dict[str, Any]:
    if not account_no or not ifsc:
        return {"match": False, "reason": "Bank account number or IFSC is missing."}

    account_ok = account_no.isdigit() and 9 <= len(account_no) <= 18
    ifsc_ok = len(ifsc) == 11 and ifsc[:4].isalpha()
    return {
        "match": account_ok and ifsc_ok,
        "reason": None
        if account_ok and ifsc_ok
        else "Bank account number or IFSC format is invalid.",
    }


async def verification_node(state: Any) :
    print("Verifying data...")
    