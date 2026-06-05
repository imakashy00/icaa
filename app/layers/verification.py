from __future__ import annotations

from difflib import SequenceMatcher
from typing import Any, Dict, Optional


def _normalize(value: Optional[str]) -> str:
	return (value or "").strip().casefold()


def _similarity(left: Optional[str], right: Optional[str]) -> float:
	if not left or not right:
		return 0.0
	return SequenceMatcher(None, _normalize(left), _normalize(right)).ratio()


def compare_identity(extracted_name: Optional[str], evidence_name: Optional[str]) -> Dict[str, Any]:
	score = _similarity(extracted_name, evidence_name)
	return {
		"match": score >= 0.85,
		"similarity_score": score,
		"reason": None if score >= 0.85 else "Claimant name does not sufficiently match policy holder name.",
	}


def verify_policy(policy: Optional[Dict[str, Any]], policy_no: Optional[str]) -> Dict[str, Any]:
	if not policy:
		return {"match": False, "reason": "Policy record not found."}

	matches_policy_no = policy_no == policy.get("policy_no")
	is_active = bool(policy.get("active"))
	return {
		"match": matches_policy_no and is_active,
		"reason": None if matches_policy_no and is_active else "Policy number mismatch or policy is inactive.",
		"policy_active": is_active,
	}


def verify_hospital(extracted_hospital_name: Optional[str], evidence_hospital: Optional[Dict[str, Any]]) -> Dict[str, Any]:
	if not evidence_hospital:
		return {"match": False, "reason": "Hospital record not found."}

	score = _similarity(extracted_hospital_name, evidence_hospital.get("hospital_name"))
	in_network = bool(evidence_hospital.get("in_network"))
	return {
		"match": score >= 0.85 and in_network,
		"similarity_score": score,
		"in_network": in_network,
		"reason": None if score >= 0.85 and in_network else "Hospital does not match or is not in network.",
	}


def verify_medical_data(state: Dict[str, Any]) -> Dict[str, Any]:
	diagnosis = state.get("diagnosis")
	admission_date = state.get("admission_date")
	discharge_date = state.get("discharge_date")
	claim_form = state.get("claim_form") or {}
	diagnosis_and_treatment = claim_form.get("diagnosis_and_treatment") if isinstance(claim_form, dict) else None

	has_core_fields = bool(diagnosis or (diagnosis_and_treatment and diagnosis_and_treatment.get("diagnosis")))
	has_dates = bool(admission_date and discharge_date)

	return {
		"match": has_core_fields and has_dates,
		"reason": None if has_core_fields and has_dates else "Medical details are incomplete or missing hospitalization dates.",
	}


def verify_bank_details(account_no: Optional[str], ifsc: Optional[str]) -> Dict[str, Any]:
	if not account_no or not ifsc:
		return {"match": False, "reason": "Bank account number or IFSC is missing."}

	account_ok = account_no.isdigit() and 9 <= len(account_no) <= 18
	ifsc_ok = len(ifsc) == 11 and ifsc[:4].isalpha()
	return {
		"match": account_ok and ifsc_ok,
		"reason": None if account_ok and ifsc_ok else "Bank account number or IFSC format is invalid.",
	}


async def verification_node(state: Dict[str, Any]) -> Dict[str, Any]:
	evidence_bundle = state.get("evidence_bundle", {})
	claim_form = state.get("claim_form") or {}
	primary_insured = claim_form.get("primary_insured") if isinstance(claim_form, dict) else None
	hospital_details = claim_form.get("hospital_details") if isinstance(claim_form, dict) else None

	claimant_name = state.get("insured_name") or state.get("patient_name")
	evidence_name = evidence_bundle.get("policy_holder_name") or evidence_bundle.get("claimant", {}).get("policy_holder_name")

	identity_result = compare_identity(claimant_name, evidence_name)
	policy_result = verify_policy(evidence_bundle.get("policy"), state.get("policy_no"))
	hospital_result = verify_hospital(
		state.get("hospital_name") or (hospital_details or {}).get("hospital_name"),
		evidence_bundle.get("hospital"),
	)
	medical_result = verify_medical_data(state)
	bank_result = verify_bank_details(state.get("bank_account_no"), state.get("ifsc_or_routing_code"))

	workflow_history = list(state.get("workflow_history", []))
	workflow_history.append("VerificationAgent: compared extracted claim data with policy, hospital, medical, and bank evidence")

	verification_updates = {
		"identity_verified": identity_result["match"],
		"policy_verified": policy_result["match"],
		"hospital_verified": hospital_result["match"],
		"medical_verified": medical_result["match"],
		"bank_verified": bank_result["match"],
		"verification_results": {
			"identity": identity_result,
			"policy": policy_result,
			"hospital": hospital_result,
			"medical": medical_result,
			"bank": bank_result,
		},
		"workflow_history": workflow_history,
		"current_agent": "VerificationAgent",
		"next_step": "policy_analysis",
	}

	if primary_insured is not None:
		verification_updates["claimant_name_similarity"] = identity_result.get("similarity_score", 0.0)

	return verification_updates