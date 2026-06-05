from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path
from typing import Any, Dict, List, cast

from dotenv import load_dotenv


from app.graph.orchestrator import app
from app.graph.types import ClaimState
from app.layers.audit import audit_node
from app.layers.decision import decision_node
from app.layers.evidence_aggregation import evidence_node
from app.layers.fraud_analysis import analyze_fraud
from app.layers.policy_analysis import policy_analysis_node
from app.layers.verification import verification_node
# Ensure .env is loaded early so OPENAI_API_KEY is available to imported modules
load_dotenv()


def _read_claim_data(claim_path: Path) -> Dict[str, Any]:
    with claim_path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _as_bool(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().casefold()
        if normalized in {"yes", "true", "1"}:
            return True
        if normalized in {"no", "false", "0"}:
            return False
    return None


def _as_float(value: Any) -> float | None:
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return None
    return None


def _build_claim_form(claim_data: Dict[str, Any]) -> Dict[str, Any]:
    primary_insured = claim_data.get("primary_insured", {})
    insurance_history = claim_data.get("insurance_history", {})
    patient_details = claim_data.get("patient_details", {})
    admitted_patient_details = claim_data.get("admitted_patient_details", {})
    claim_details = claim_data.get("claim_details", {})
    hospital_details = claim_data.get("hospital_details", {})
    diagnosis_details = claim_data.get("diagnosis_and_treatment_details", {})
    bank_details = claim_data.get("bank_details", {})
    declaration = claim_data.get("claimant_declaration", {})

    expenses = claim_details.get("expenses", {})
    diagnosis_codes = diagnosis_details.get("medical_codes", {}).get(
        "icd_10_diagnosis", {}
    )
    injury_details = diagnosis_details.get("injury_or_accident_details", {})

    claim_form = {
        "primary_insured": {
            "policy_no": primary_insured.get("policy_no"),
            "tpa_id": primary_insured.get("tpa_id"),
            "policy_holder_name": primary_insured.get("policy_holder_name"),
            "address": primary_insured.get("address"),
            "city": primary_insured.get("city"),
            "state": primary_insured.get("state"),
            "pin_code": primary_insured.get("pin_code"),
            "phone": primary_insured.get("phone"),
            "email": primary_insured.get("email"),
        },
        "insurance_history": {
            "other_medical_insurance": _as_bool(
                insurance_history.get("other_medical_insurance")
            ),
            "commencement_without_break_date": insurance_history.get(
                "commencement_without_break_date"
            ),
            "insurance_company_name": insurance_history.get("insurance_company_name"),
            "previous_policy_no": insurance_history.get("policy_no"),
            "sum_insured": _as_float(insurance_history.get("sum_insured")),
            "hospitalized_in_last_four_years": _as_bool(
                insurance_history.get("hospitalized_in_last_four_years")
            ),
        },
        "patient_details": {
            "patient_name": patient_details.get("name")
            or admitted_patient_details.get("patient_name"),
            "relationship_to_policy_holder": patient_details.get(
                "relationship_to_policy_holder"
            ),
            "gender": patient_details.get("gender"),
            "age": patient_details.get("age"),
            "date_of_birth": patient_details.get("date_of_birth"),
            "occupation": patient_details.get("occupation"),
            "room_category": patient_details.get("room_category"),
            "hospitalization_reason": patient_details.get("hospitalsation_reason")
            or patient_details.get("hospitalization_reason"),
            "system_of_medicine": patient_details.get("system_of_medicine"),
        },
        "hospitalization_details": {
            "date_of_admission": admitted_patient_details.get("date_of_admission")
            or patient_details.get("date_of_admission"),
            "time_of_admission": admitted_patient_details.get("time_of_admission")
            or patient_details.get("time_of_admission"),
            "date_of_discharge": admitted_patient_details.get("date_of_discharge")
            or patient_details.get("date_of_discharge"),
            "time_of_discharge": admitted_patient_details.get("time_of_discharge")
            or patient_details.get("time_of_discharge"),
            "type_of_admission": admitted_patient_details.get("type_of_admission"),
            "status_at_discharge": admitted_patient_details.get("status_at_discharge"),
        },
        "claim_expenses": {
            "hospitalization_expenses": _as_float(
                expenses.get("hospitalization_expenses", {}).get("amount_rs")
            ),
            "pre_hospitalization_expenses": _as_float(
                expenses.get("pre_hospitalization_expenses", {}).get("amount_rs")
            ),
            "pre_hospitalization_period_days": expenses.get(
                "pre_hospitalization_expenses", {}
            ).get("period_days"),
            "post_hospitalization_expenses": _as_float(
                expenses.get("post_hospitalization_expenses", {}).get("amount_rs")
            ),
            "post_hospitalization_period_days": expenses.get(
                "post_hospitalization_expenses", {}
            ).get("period_days"),
            "health_checkup_cost": _as_float(
                expenses.get("health_check_up_cost", {}).get("amount_rs")
            ),
            "ambulance_charges": _as_float(
                expenses.get("ambulance_charges", {}).get("amount_rs")
            ),
            "other_expenses": _as_float(expenses.get("others", {}).get("amount_rs")),
            "total_expenses": _as_float(expenses.get("total_expenses_rs")),
        },
        "benefits": {
            "hospital_daily_cash": _as_float(
                claim_details.get("benefits", {}).get("hospital_daily_cash_rs")
            ),
            "surgical_cash": _as_float(
                claim_details.get("benefits", {}).get("surgical_cash_rs")
            ),
            "critical_illness_benefit": _as_float(
                claim_details.get("benefits", {}).get("critical_illness_benefit_rs")
            ),
            "convalescence_benefit": _as_float(
                claim_details.get("benefits", {}).get("convalescence_rs")
            ),
            "pre_post_lump_sum_benefit": _as_float(
                claim_details.get("benefits", {}).get(
                    "pre_post_hospitalization_lump_sum_benefit_rs"
                )
            ),
            "other_benefits": _as_float(
                claim_details.get("benefits", {}).get("others_rs")
            ),
            "total_lump_sum_benefit": _as_float(
                claim_details.get("benefits", {}).get("total_lump_sum_rs")
            ),
        },
        "document_checklist": {
            "claim_form_submitted": _as_bool(
                claim_details.get("claim_documents_submitted_checklist", {}).get(
                    "duly_filled_and_signed_claim_form"
                )
            ),
            "intimation_letter_submitted": _as_bool(
                claim_details.get("claim_documents_submitted_checklist", {}).get(
                    "copy_of_intimation_letter_if_any"
                )
            ),
            "hospital_main_bill_submitted": _as_bool(
                claim_details.get("claim_documents_submitted_checklist", {}).get(
                    "hospital_main_bill"
                )
            ),
            "hospital_breakup_bill_submitted": _as_bool(
                claim_details.get("claim_documents_submitted_checklist", {}).get(
                    "hospital_break_up_bill"
                )
            ),
            "payment_receipt_submitted": _as_bool(
                claim_details.get("claim_documents_submitted_checklist", {}).get(
                    "hospital_bill_payment_receipt"
                )
            ),
            "discharge_summary_submitted": _as_bool(
                claim_details.get("claim_documents_submitted_checklist", {}).get(
                    "hospital_discharge_summary"
                )
            ),
            "doctor_prescription_submitted": _as_bool(
                claim_details.get("claim_documents_submitted_checklist", {}).get(
                    "doctor_prescription"
                )
            ),
            "investigation_request_submitted": _as_bool(
                claim_details.get("claim_documents_submitted_checklist", {}).get(
                    "doctor_request_for_investigation"
                )
            ),
            "investigation_reports_submitted": _as_bool(
                claim_details.get("claim_documents_submitted_checklist", {}).get(
                    "investigation_reports_including_ct_mri_usg_hpe"
                )
            ),
            "operation_theatre_notes_submitted": _as_bool(
                claim_details.get("claim_documents_submitted_checklist", {}).get(
                    "operation_theater_notes"
                )
            ),
            "ecg_submitted": _as_bool(
                claim_details.get("claim_documents_submitted_checklist", {}).get("ecg")
            ),
            "pharmacy_bill_submitted": _as_bool(
                claim_details.get("claim_documents_submitted_checklist", {}).get(
                    "pharmacy_bill"
                )
            ),
            "other_documents_submitted": _as_bool(
                claim_details.get("claim_documents_submitted_checklist", {}).get(
                    "others"
                )
            ),
        },
        "hospital_details": {
            "hospital_name": hospital_details.get("hospital_name"),
            "hospital_id": hospital_details.get("hospital_id"),
            "hospital_address": hospital_details.get("hospital_address"),
            "hospital_type": hospital_details.get("hospital_type"),
            "doctor_name": hospital_details.get("doctor_name"),
            "doctor_qualification": hospital_details.get("qualification"),
            "doctor_registration_no": hospital_details.get(
                "registaration_with_state-code"
            ),
            "diagnosis": hospital_details.get("diagnosis"),
            "procedure": hospital_details.get("procedure"),
            "treating_doctor": hospital_details.get("treating_doctor"),
        },
        "diagnosis_and_treatment": {
            "diagnosis": {
                "primary_icd_code": diagnosis_codes.get("primary", {}).get("code"),
                "primary_icd_description": diagnosis_codes.get("primary", {}).get(
                    "description"
                ),
                "secondary_icd_code": diagnosis_codes.get("additional", {}).get("code"),
                "secondary_icd_description": diagnosis_codes.get("additional", {}).get(
                    "description"
                ),
            },
            "comorbidities": [
                {
                    "code": item.get("code"),
                    "description": item.get("description"),
                }
                for item in diagnosis_codes.get("co_morbidities", [])
                if isinstance(item, dict)
            ],
            "procedures": [
                {
                    "code": item.get("code"),
                    "description": item.get("description"),
                }
                for item in diagnosis_details.get("medical_codes", {})
                .get("procedure_or_surgery_codes", {})
                .get("procedures", [])
                if isinstance(item, dict)
            ],
            "procedure_notes": diagnosis_details.get("medical_codes", {})
            .get("procedure_or_surgery_codes", {})
            .get("detailed_notes"),
            "pre_authorization": {
                "is_obtained": _as_bool(
                    diagnosis_details.get("pre_authorization", {}).get("is_obtained")
                ),
                "approval_number": diagnosis_details.get("pre_authorization", {}).get(
                    "approval_number"
                ),
                "rejection_or_missing_reason": diagnosis_details.get(
                    "pre_authorization", {}
                ).get("rejection_or_missing_reason"),
            },
            "injury_details": {
                "is_injury": _as_bool(injury_details.get("is_injury")),
                "cause_type": injury_details.get("cause_type"),
                "alcohol_or_substance_abuse_suspected": _as_bool(
                    injury_details.get("substance_abuse_or_alcohol", {}).get(
                        "is_suspected"
                    )
                ),
                "medico_legal_case": _as_bool(
                    injury_details.get("legal_and_police_records", {}).get(
                        "is_medico_legal_case"
                    )
                ),
                "police_reported": _as_bool(
                    injury_details.get("legal_and_police_records", {}).get(
                        "is_reported_to_police"
                    )
                ),
                "fir_number": injury_details.get("legal_and_police_records", {}).get(
                    "fir_number"
                ),
            },
        },
        "bank_details": {
            "beneficiary_name": bank_details.get("beneficiary_name"),
            "bank_name": bank_details.get("bank_name"),
            "account_no": bank_details.get("account_no"),
            "ifsc": bank_details.get("ifsc"),
        },
        "declaration": {
            "declaration_text": declaration.get("declaration_text"),
            "signature_name": declaration.get("signature_name"),
            "signature_date": declaration.get("signature_date"),
        },
    }

    return claim_form


def _format_document(title: str, sections: List[tuple[str, Any]]) -> str:
    lines = [title, ""]
    for heading, value in sections:
        lines.append(f"{heading}:")
        lines.append(json.dumps(value, indent=2, ensure_ascii=False, default=str))
        lines.append("")
    return "\n".join(lines).strip()


def _build_initial_state(claim_data: Dict[str, Any]) -> Dict[str, Any]:
    claim_form = _build_claim_form(claim_data)

    return {
        "claim_id": claim_data.get("claim_id"),
        "uploaded_files": claim_data.get("uploaded_files", []),
        "raw_text": json.dumps(claim_data, indent=2, ensure_ascii=False, default=str),
        "claim_form": claim_form,
        "policy_no": claim_form.get("primary_insured", {}).get("policy_no"),
        "company_tpa_id": claim_form.get("primary_insured", {}).get("tpa_id"),
        "insured_name": claim_form.get("primary_insured", {}).get("policy_holder_name"),
        "patient_name": claim_form.get("patient_details", {}).get("patient_name"),
        "relationship_to_insured": claim_form.get("patient_details", {}).get(
            "relationship_to_policy_holder"
        ),
        "room_category": claim_form.get("patient_details", {}).get("room_category"),
        "hospitalization_reason": claim_form.get("patient_details", {}).get(
            "hospitalization_reason"
        ),
        "hospital_name": claim_form.get("hospital_details", {}).get("hospital_name"),
        "hospital_type": claim_form.get("hospital_details", {}).get("hospital_type"),
        "diagnosis": claim_form.get("hospital_details", {}).get("diagnosis"),
        "primary_icd_code": claim_form.get("diagnosis_and_treatment", {})
        .get("diagnosis", {})
        .get("primary_icd_code"),
        "admission_date": claim_form.get("hospitalization_details", {}).get(
            "date_of_admission"
        ),
        "discharge_date": claim_form.get("hospitalization_details", {}).get(
            "date_of_discharge"
        ),
        "hospitalization_expenses": claim_form.get("claim_expenses", {}).get(
            "hospitalization_expenses"
        ),
        "pre_hospitalization_expenses": claim_form.get("claim_expenses", {}).get(
            "pre_hospitalization_expenses"
        ),
        "post_hospitalization_expenses": claim_form.get("claim_expenses", {}).get(
            "post_hospitalization_expenses"
        ),
        "ambulance_charges": claim_form.get("claim_expenses", {}).get(
            "ambulance_charges"
        ),
        "total_claim_amount": claim_form.get("claim_expenses", {}).get("total_expenses")
        or 0.0,
        "bank_account_no": claim_form.get("bank_details", {}).get("account_no"),
        "ifsc_or_routing_code": claim_form.get("bank_details", {}).get("ifsc"),
        "submitted_docs": claim_data.get("uploaded_files", []),
        "missing_docs": [],
        "document_validation_status": "seeded",
        "extraction_confidence": 1.0,
        "extraction_errors": [],
        "evidence_bundle": {},
        "verification_results": {},
        "identity_verified": False,
        "policy_verified": False,
        "hospital_verified": False,
        "medical_verified": False,
        "bank_verified": False,
        "fraud_score": 0.0,
        "fraud_flags": [],
        "fraud_deduction_pct": 0.0,
        "duplicate_claim_detected": False,
        "suspicious_patterns": [],
        "policy_active": False,
        "coverage_eligible": False,
        "waiting_period_completed": False,
        "exclusions_found": [],
        "approved_coverage_amount": None,
        "policy_analysis": {},
        "final_decision": None,
        "rejection_reason": None,
        "approved_amount": None,
        "final_report": {},
        "audit_summary": {},
        "current_agent": "ClaimDriver",
        "next_step": "evidence_aggregation",
        "workflow_history": [
            "MainDriver: loaded claim_data.json and prepared workflow state"
        ],
    }


def _build_document_texts(
    claim_data: Dict[str, Any], claim_form: Dict[str, Any]
) -> Dict[str, str]:
    texts: Dict[str, str] = {}
    texts["claim_form"] = _format_document("Claim Form", [("claim_form", claim_form)])
    texts["raw_json"] = _format_document("Raw Claim JSON", [("raw", claim_data)])
    for fname in claim_data.get("uploaded_files", []) or []:
        texts[str(fname)] = _format_document(
            f"Uploaded File: {fname}", [("claim_form", claim_form), ("raw", claim_data)]
        )
    return texts


async def _run_downstream_agents(initial_state: Dict[str, Any]) -> Dict[str, Any]:
    state = dict(initial_state)
    for node in (evidence_node, verification_node, policy_analysis_node):
        state.update(await node(state))

    state.update(analyze_fraud(state))
    state.update(await decision_node(state))
    state.update(await audit_node(state))
    return state


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the insurance claim workflow against claim_data.json"
    )
    parser.add_argument(
        "claim_file",
        nargs="?",
        default=str(Path(__file__).resolve().with_name("claim_data.json")),
        help="Path to the submitted claim JSON file",
    )
    parser.add_argument(
        "--use-graph",
        dest="use_graph",
        action="store_true",
        help="Invoke the compiled StateGraph pipeline (runs classifier/extractor, requires OPENAI_API_KEY)",
    )

    args = parser.parse_args()

    claim_path = Path(args.claim_file).expanduser().resolve()
    claim_data = _read_claim_data(claim_path)
    initial_state = _build_initial_state(claim_data)

    # populate document_texts so graph nodes that expect OCR/text have data
    initial_state["document_texts"] = _build_document_texts(
        claim_data, initial_state.get("claim_form", {})
    )

    if getattr(args, "use_graph", False):
        # run through the compiled StateGraph (may exercise LLM nodes)
        # use the async API so async node functions (LLM calls) are supported
        result = asyncio.run(app.ainvoke(cast(ClaimState, initial_state)))
    else:
        result = asyncio.run(
            _run_downstream_agents(cast(Dict[str, Any], initial_state))
        )

    print(
        json.dumps(
            {
                "claim_id": claim_data.get("claim_id"),
                "final_decision": result.get("final_decision"),
                "rejection_reason": result.get("rejection_reason"),
                "approved_amount": result.get("approved_amount"),
                "final_report": result.get("final_report"),
                "audit_summary": result.get("audit_summary"),
                "workflow_history": result.get("workflow_history"),
            },
            indent=2,
            ensure_ascii=False,
            default=str,
        )
    )


if __name__ == "__main__":
    main()
