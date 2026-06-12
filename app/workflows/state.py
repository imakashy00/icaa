from __future__ import annotations
from typing import Annotated, Any, Dict, List, Optional
import operator

from pydantic import BaseModel
# from app.schemas.claim_form import BankDetails, BenefitDetails, ClaimExpenses, DocumentChecklist, HospitalDetails, InsuranceHistory, PatientDetails, PolicyRecord, PrescriptionRecord, PrimaryInsured


# class ClaimState(BaseModel):

#     document_text:Optional[str] 

#     primary_insured: PrimaryInsured
#     insurance_history: InsuranceHistory
#     patient_details:PatientDetails
#     prescriptions: List[PrescriptionRecord]
#     hospital_details:HospitalDetails
#     bank_details: BankDetails
#     claim_details:ClaimExpenses
#     benefit_details:BenefitDetails
#     docs_checklist:DocumentChecklist
#     policy_record:PolicyRecord

#     # Fraud Details
#     fraud_score: float
#     fraud_flags: Annotated[List[str], operator.add]

#     # Human Review
#     final_decision: Optional[str]
#     rejection_reason: Optional[str]
#     approved_amount: Optional[float]
#     final_report: Dict[str, Any]
#     audit_summary: Dict[str, Any]

#     # Workflow Control
#     current_agent: Optional[str]
#     next_step: Optional[str]
#     workflow_history: List[str]

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class PrimaryInsured(BaseModel):
    policy_no: str = ""
    tpa_id: str = ""
    policy_holder_name: str = ""
    address: str = ""
    city: str = ""
    state: str = ""
    pin_code: str = ""
    phone: Optional[str] = None
    email: str = ""


class InsuranceHistory(BaseModel):
    other_medical_insurance: bool = False
    commencement_without_break_date: Optional[str] = None
    insurance_company_name: str = ""
    previous_policy_no: str = ""
    sum_insured: float = 0.0
    hospitalized_in_last_four_years: bool = False


class PatientDetails(BaseModel):
    patient_name: str = ""
    relationship_to_policy_holder: str = ""
    gender: Optional[str] = None
    age: Optional[int] = None
    date_of_birth: Optional[str] = None
    occupation: Optional[str] = None
    room_category: str = "single_occupancy"
    hospitalization_reason: str = "illness"
    system_of_medicine: str = "allopathy"


class PrescriptionMedication(BaseModel):
    name: str = ""
    strength: str = ""
    form: str = ""
    dosage: str = ""
    frequency: str = ""
    duration_days: int = 0
    instructions: str = ""


class PrescriptionRecord(BaseModel):
    prescription_id: str = ""
    date: str = ""
    prescriber_name: str = ""
    registration_no: str = ""
    clinic: str = ""
    medications: List[PrescriptionMedication] = Field(
        default=[
            PrescriptionMedication(
                name="",
                strength="",
                form="",
                dosage="",
                frequency="",
                duration_days=0,
                instructions="",
            )
        ]
    )
    notes: str = ""
    file: str = ""


class HospitalDetails(BaseModel):
    hospital_name: str = ""
    hospital_id: str = ""
    hospital_address: str = ""
    hospital_type: str = "network"
    doctor_name: str = ""
    doctor_qualification: str = ""
    doctor_registration_no: str = ""
    diagnosis: str = ""
    procedure: str = ""
    treating_doctor: str = ""


class BankDetails(BaseModel):
    beneficiary_name: str = ""
    bank_name: str = ""
    account_no: str = ""
    ifsc: str = ""


class ClaimExpenses(BaseModel):
    hospitalization_expenses: float = 0.0
    pre_hospitalization_expenses: float = 0.0
    pre_hospitalization_period_days: int = 0
    post_hospitalization_expenses: float = 0.0
    post_hospitalization_period_days: int = 0
    health_checkup_cost: float = 0.0
    ambulance_charges: float = 0.0
    other_expenses: float = 0.0
    total_expenses: float = 0.0


class BenefitDetails(BaseModel):
    hospital_daily_cash: float = 0.0
    surgical_cash: float = 0.0
    critical_illness_benefit: float = 0.0
    convalescence_benefit: float = 0.0
    pre_post_lump_sum_benefit: float = 0.0
    other_benefits: float = 0.0
    total_lump_sum_benefit: float = 0.0


class DocumentChecklist(BaseModel):
    claim_form_submitted: bool = False
    intimation_letter_submitted: bool = False
    hospital_main_bill_submitted: bool = False
    hospital_breakup_bill_submitted: bool = False
    payment_receipt_submitted: bool = False
    discharge_summary_submitted: bool = False
    doctor_prescription_submitted: bool = False
    investigation_request_submitted: bool = False
    investigation_reports_submitted: bool = False
    operation_theatre_notes_submitted: bool = False
    ecg_submitted: bool = False
    pharmacy_bill_submitted: bool = False
    other_documents_submitted: bool = False


class PolicyRecord(BaseModel):
    policy_no: str = ""
    tpa_id: str = ""
    policy_holder_name: str = ""
    active: bool = True
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    waiting_period_days: Optional[int] = None
    sum_insured: float = 0.0
    room_rent_cap_per_day: Optional[float] = None
    co_pay_percentage: Optional[float] = None
    exclusions: List[str] = Field(default_factory=list)
    covered_icd_codes: List[str] = Field(default_factory=list)
    covered_conditions: List[str] = Field(default_factory=list)


class ClaimState(BaseModel):
    document_text:str  = Field(default="")
    primary_insured: PrimaryInsured = Field(default_factory=PrimaryInsured)
    insurance_history: InsuranceHistory = Field(default_factory=InsuranceHistory)
    patient_details: PatientDetails = Field(default_factory=PatientDetails)
    prescriptions: List[PrescriptionRecord] = Field(default_factory=list)    
    hospital_details: HospitalDetails = Field(default_factory=HospitalDetails)
    bank_details: BankDetails = Field(default_factory=BankDetails)
    claim_details: ClaimExpenses = Field(default_factory=ClaimExpenses)
    benefit_details: BenefitDetails = Field(default_factory=BenefitDetails)
    docs_checklist: DocumentChecklist = Field(default_factory=DocumentChecklist)
    policy_record: PolicyRecord = Field(default_factory=PolicyRecord)
    fraud_score: float = 0.0
    fraud_flags: List[str] = Field(default_factory=list)
    final_decision: Optional[str] = None
    rejection_reason: Optional[str] = None
    approved_amount: Optional[float] = None
    final_report: Dict[str, Any] = Field(default_factory=dict)
    audit_summary: Dict[str, Any] = Field(default_factory=dict)
    current_agent: Optional[str] = None
    next_step: Optional[str] = "data_extraction"
    workflow_history: List[Dict[str, Any]] = Field(default_factory=list)
