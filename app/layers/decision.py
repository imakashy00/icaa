from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List


def _passed_checks(state: Dict[str, Any]) -> Dict[str, bool]:
	return {
		"identity_verified": bool(state.get("identity_verified")),
		"policy_verified": bool(state.get("policy_verified")),
		"hospital_verified": bool(state.get("hospital_verified")),
		"medical_verified": bool(state.get("medical_verified")),
		"bank_verified": bool(state.get("bank_verified")),
		"policy_active": bool(state.get("policy_active")),
		"coverage_eligible": bool(state.get("coverage_eligible")),
		"waiting_period_completed": bool(state.get("waiting_period_completed")),
		"duplicate_claim_detected": not bool(state.get("duplicate_claim_detected")),
	}


def _failed_checks(state: Dict[str, Any]) -> Dict[str, List[str]]:
	failed: List[str] = []

	verification_results = state.get("verification_results", {})
	for name, result in verification_results.items():
		if isinstance(result, dict) and not result.get("match", False):
			reason = result.get("reason") or f"{name.title()} verification failed."
			failed.append(reason)

	for exclusion in state.get("exclusions_found", []) or []:
		failed.append(str(exclusion))

	for flag in state.get("fraud_flags", []) or []:
		failed.append(str(flag))

	return {"reasons": failed}


def build_final_report(state: Dict[str, Any]) -> Dict[str, Any]:
	failed_reasons = _failed_checks(state)["reasons"]
	passed_checks = _passed_checks(state)

	approved_amount = float(state.get("approved_coverage_amount") or 0.0)
	fraud_score = float(state.get("fraud_score") or 0.0)
	extraction_confidence = float(state.get("extraction_confidence") or 0.0)

	if failed_reasons:
		final_decision = "Rejected" if fraud_score >= 50 or not state.get("coverage_eligible", False) else "Pending Human Review"
	elif fraud_score < 10 and extraction_confidence >= 0.95:
		final_decision = "Approved"
	else:
		final_decision = "Pending Human Review"

	rejection_reason = None
	if final_decision == "Rejected" and failed_reasons:
		rejection_reason = "; ".join(failed_reasons)

	if final_decision == "Rejected":
		approved_amount = 0.0

	deductions = state.get("policy_analysis", {}).get("approval_result", {}).get("deductions", [])

	return {
		"passed_checks": passed_checks,
		"failed_checks": failed_reasons,
		"financial": {
			"claimed_amount": float(state.get("policy_analysis", {}).get("approval_result", {}).get("claimed_amount") or state.get("total_claim_amount") or 0.0),
			"approved_amount": round(approved_amount, 2),
			"deductions": deductions,
		},
		"decision": final_decision,
		"rejection_reason": rejection_reason,
		"fraud_score": fraud_score,
		"generated_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
	}


async def decision_node(state: Dict[str, Any]) -> Dict[str, Any]:
	final_report = build_final_report(state)
	workflow_history = list(state.get("workflow_history", []))
	workflow_history.append(f"DecisionAgent: final decision set to {final_report['decision']}")

	return {
		"final_decision": final_report["decision"],
		"rejection_reason": final_report["rejection_reason"],
		"approved_amount": final_report["financial"]["approved_amount"],
		"final_report": final_report,
		"workflow_history": workflow_history,
		"current_agent": "DecisionAgent",
		"next_step": "audit",
	}