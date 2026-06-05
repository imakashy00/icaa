from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional


def _parse_date(value: Optional[str]) -> Optional[datetime]:
	if not value:
		return None

	for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%d/%m/%y"):
		try:
			return datetime.strptime(value, fmt)
		except ValueError:
			continue
	return None


def _sum_claim_expenses(claim_expenses: Optional[Dict[str, Any]]) -> Dict[str, Any]:
	if not claim_expenses:
		return {
			"declared_total": None,
			"computed_total": 0.0,
			"line_items": {},
			"validation_warning": None,
		}

	line_items: Dict[str, float] = {}
	for key in (
		"hospitalization_expenses",
		"pre_hospitalization_expenses",
		"post_hospitalization_expenses",
		"ambulance_charges",
		"health_checkup_cost",
		"other_expenses",
	):
		value = claim_expenses.get(key)
		if isinstance(value, (int, float)):
			line_items[key] = float(value)

	computed_total = round(sum(line_items.values()), 2)
	declared_total = claim_expenses.get("total_expenses")
	if isinstance(declared_total, (int, float)):
		declared_total = float(declared_total)
	else:
		declared_total = None

	validation_warning = None
	if declared_total is not None and abs(computed_total - declared_total) > 1.0:
		validation_warning = (
			f"Declared total_expenses ({declared_total:.2f}) does not reconcile with itemized expenses ({computed_total:.2f})."
		)

	return {
		"declared_total": declared_total,
		"computed_total": computed_total,
		"line_items": line_items,
		"validation_warning": validation_warning,
	}


def check_diagnosis_coverage(icd_code: Optional[str], policy: Optional[Dict[str, Any]]) -> Dict[str, Any]:
	if not policy:
		return {"coverage_eligible": False, "reason": "Policy record not available."}

	exclusions = policy.get("exclusions", [])
	covered_icd_codes = policy.get("covered_icd_codes", [])
	covered_conditions = policy.get("covered_conditions", [])
	diagnosis_code = (icd_code or "").strip().upper()

	code_covered = diagnosis_code in {code.upper() for code in covered_icd_codes}
	return {
		"coverage_eligible": code_covered,
		"reason": None if code_covered else "Diagnosis is not listed as covered under the policy rules.",
		"exclusions": exclusions,
		"covered_conditions": covered_conditions,
	}


def calculate_approved_amount(
	claim_expenses: Optional[Dict[str, Any]],
	policy: Optional[Dict[str, Any]],
	coverage_eligible: bool,
	fraud_deduction_pct: float,
) -> Dict[str, Any]:
	amounts = _sum_claim_expenses(claim_expenses)
	declared_total = amounts["declared_total"]
	computed_total = amounts["computed_total"]
	claimed_amount = declared_total if declared_total is not None else computed_total
	if not policy or not coverage_eligible:
		return {
			"claimed_amount": claimed_amount,
			"approved_amount": 0.0,
			"deductions": [],
			"validation_warnings": [amounts["validation_warning"]] if amounts["validation_warning"] else [],
			"reason": "Claim is not eligible for policy coverage.",
		}

	room_rent_cap = float(policy.get("room_rent_cap_per_day") or 0.0)
	sum_insured = float(policy.get("sum_insured") or 0.0)
	co_pay_percentage = float(policy.get("co_pay_percentage") or 0.0)

	approved_amount = claimed_amount
	deductions = []
	validation_warnings = [amounts["validation_warning"]] if amounts["validation_warning"] else []

	line_items = amounts["line_items"]

	hospitalization_expenses = float(line_items.get("hospitalization_expenses") or 0.0)
	if room_rent_cap and hospitalization_expenses > room_rent_cap:
		deductions.append({
			"reason": "Hospitalization expenses capped by room rent / policy limit",
			"amount": hospitalization_expenses - room_rent_cap,
		})
		approved_amount -= hospitalization_expenses - room_rent_cap

	if approved_amount > sum_insured:
		deductions.append({
			"reason": "Claim amount exceeds sum insured",
			"amount": approved_amount - sum_insured,
		})
		approved_amount = sum_insured

	if co_pay_percentage > 0:
		co_pay_amount = approved_amount * (co_pay_percentage / 100.0)
		deductions.append({"reason": "Policy co-pay applied", "amount": co_pay_amount})
		approved_amount -= co_pay_amount

	if fraud_deduction_pct > 0:
		fraud_amount = approved_amount * (fraud_deduction_pct / 100.0)
		deductions.append({"reason": "Fraud risk deduction applied", "amount": fraud_amount})
		approved_amount -= fraud_amount

	approved_amount = max(0.0, round(approved_amount, 2))

	return {
		"claimed_amount": round(claimed_amount, 2),
		"approved_amount": approved_amount,
		"deductions": deductions,
		"validation_warnings": validation_warnings,
		"reason": None,
	}


async def policy_analysis_node(state: Dict[str, Any]) -> Dict[str, Any]:
	evidence_bundle = state.get("evidence_bundle", {})
	policy = evidence_bundle.get("policy")
	claim_form = state.get("claim_form") or {}
	diagnosis_and_treatment = claim_form.get("diagnosis_and_treatment") if isinstance(claim_form, dict) else {}
	diagnosis = (diagnosis_and_treatment or {}).get("diagnosis") or {}

	coverage_result = check_diagnosis_coverage(diagnosis.get("primary_icd_code") or state.get("primary_icd_code") or state.get("diagnosis_code"), policy)

	admission_date = _parse_date(state.get("admission_date"))
	policy_start_date = _parse_date(policy.get("start_date")) if policy else None
	waiting_period_days = int((policy or {}).get("waiting_period_days") or 0)
	waiting_period_completed = True
	if admission_date and policy_start_date:
		waiting_period_completed = (admission_date - policy_start_date).days >= waiting_period_days

	exclusions_found = []
	if not coverage_result["coverage_eligible"]:
		exclusions_found.append(coverage_result["reason"])
	if approval_result.get("validation_warnings"):
		exclusions_found.extend([warning for warning in approval_result["validation_warnings"] if warning])

	claim_expenses = claim_form.get("claim_expenses") if isinstance(claim_form, dict) else {}
	fraud_deduction_pct = float(state.get("fraud_score") or 0.0)
	approval_result = calculate_approved_amount(
		claim_expenses=claim_expenses,
		policy=policy,
		coverage_eligible=coverage_result["coverage_eligible"] and waiting_period_completed,
		fraud_deduction_pct=fraud_deduction_pct,
	)

	workflow_history = list(state.get("workflow_history", []))
	workflow_history.append("PolicyAgent: evaluated diagnosis coverage, waiting period, exclusions, and approved amount")

	return {
		"policy_active": bool(policy and policy.get("active")),
		"coverage_eligible": bool(coverage_result["coverage_eligible"] and waiting_period_completed),
		"waiting_period_completed": waiting_period_completed,
		"exclusions_found": [item for item in exclusions_found if item],
		"approved_coverage_amount": approval_result["approved_amount"],
		"policy_analysis": {
			"coverage_result": coverage_result,
			"approval_result": approval_result,
			"waiting_period_days": waiting_period_days,
		},
		"workflow_history": workflow_history,
		"current_agent": "PolicyAgent",
		"next_step": "fraud_analysis",
	}