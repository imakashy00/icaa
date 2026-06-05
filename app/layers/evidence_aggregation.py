from __future__ import annotations

from datetime import datetime
from difflib import SequenceMatcher
from typing import Any, Dict, Optional

from app.data.temp_db import get_claim_history, get_claimant, get_hospital, get_policy


def _normalize(value: Optional[str]) -> str:
	return (value or "").strip().casefold()


def _name_similarity(left: Optional[str], right: Optional[str]) -> float:
	if not left or not right:
		return 0.0
	return SequenceMatcher(None, _normalize(left), _normalize(right)).ratio()


def build_evidence_bundle(state: Dict[str, Any]) -> Dict[str, Any]:
	policy_no = state.get("policy_no")
	claim_id = state.get("claim_id")
	hospital_id = state.get("hospital_id")
	hospital_name = state.get("hospital_name")

	policy = get_policy(policy_no) if policy_no else None
	claimant = get_claimant(policy_no) if policy_no else None
	claim_history = (
		get_claim_history(policy_no, exclude_claim_id=claim_id)
		if policy_no
		else []
	)
	hospital = get_hospital(hospital_id=hospital_id, hospital_name=hospital_name)

	policy_holder_name = None
	claimant_similarity = 0.0
	if claimant is not None:
		policy_holder_name = claimant.policy_holder_name
		claimant_similarity = _name_similarity(
			state.get("insured_name") or state.get("patient_name"),
			claimant.policy_holder_name,
		)

	hospital_match_score = 0.0
	if hospital is not None:
		hospital_match_score = _name_similarity(
			hospital_name or state.get("hospital_name"),
			hospital.hospital_name,
		)

	policy_is_active = bool(policy and policy.active)
	policy_matches_claim = bool(policy and policy_no == policy.policy_no)

	return {
		"claim_id": claim_id,
		"policy": policy.model_dump() if policy else None,
		"claimant": claimant.model_dump() if claimant else None,
		"claim_history": [record.model_dump() for record in claim_history],
		"hospital": hospital.model_dump() if hospital else None,
		"policy_active": policy_is_active,
		"policy_matches_claim": policy_matches_claim,
		"claimant_name_similarity": claimant_similarity,
		"hospital_name_similarity": hospital_match_score,
		"policy_holder_name": policy_holder_name,
		"fetched_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
	}


async def evidence_node(state: Dict[str, Any]) -> Dict[str, Any]:
	evidence_bundle = build_evidence_bundle(state)

	workflow_history = list(state.get("workflow_history", []))
	workflow_history.append("EvidenceAgent: loaded policy, claimant, claim history, and hospital reference data")

	return {
		"evidence_bundle": evidence_bundle,
		"policy_active": evidence_bundle["policy_active"],
		"workflow_history": workflow_history,
		"current_agent": "EvidenceAgent",
		"next_step": "verification",
	}