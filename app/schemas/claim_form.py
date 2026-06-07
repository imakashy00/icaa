from typing import List, Optional

from pydantic import BaseModel, Field


class PrimaryInsured(BaseModel):
    policy_no: Optional[str] = None
    tpa_id: Optional[str] = None
    policy_holder_name: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pin_code: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None


class InsuranceHistory(BaseModel):
    other_medical_insurance: Optional[bool] = None
    commencement_without_break_date: Optional[str] = None
    insurance_company_name: Optional[str] = None
    previous_policy_no: Optional[str] = None
    sum_insured: Optional[float] = None
    hospitalized_in_last_four_years: Optional[bool] = None


class PatientDetails(BaseModel):
    patient_name: Optional[str] = None
    relationship_to_policy_holder: Optional[str] = None
    gender: Optional[str] = None
    age: Optional[int] = None
    date_of_birth: Optional[str] = None
    occupation: Optional[str] = None
    room_category: Optional[str] = None
    hospitalization_reason: Optional[str] = None
    system_of_medicine: Optional[str] = None


class HospitalizationDetails(BaseModel):
    date_of_admission: Optional[str] = None
    time_of_admission: Optional[str] = None
    date_of_discharge: Optional[str] = None
    time_of_discharge: Optional[str] = None
    type_of_admission: Optional[str] = None
    status_at_discharge: Optional[str] = None


class ClaimExpenses(BaseModel):
    hospitalization_expenses: Optional[float] = None
    pre_hospitalization_expenses: Optional[float] = None
    pre_hospitalization_period_days: Optional[int] = None
    post_hospitalization_expenses: Optional[float] = None
    post_hospitalization_period_days: Optional[int] = None
    health_checkup_cost: Optional[float] = None
    ambulance_charges: Optional[float] = None
    other_expenses: Optional[float] = None
    total_expenses: Optional[float] = None


class BenefitDetails(BaseModel):
    hospital_daily_cash: Optional[float] = None
    surgical_cash: Optional[float] = None
    critical_illness_benefit: Optional[float] = None
    convalescence_benefit: Optional[float] = None
    pre_post_lump_sum_benefit: Optional[float] = None
    other_benefits: Optional[float] = None
    total_lump_sum_benefit: Optional[float] = None


class DocumentChecklist(BaseModel):
    claim_form_submitted: Optional[bool] = None
    intimation_letter_submitted: Optional[bool] = None
    hospital_main_bill_submitted: Optional[bool] = None
    hospital_breakup_bill_submitted: Optional[bool] = None
    payment_receipt_submitted: Optional[bool] = None
    discharge_summary_submitted: Optional[bool] = None
    doctor_prescription_submitted: Optional[bool] = None
    investigation_request_submitted: Optional[bool] = None
    investigation_reports_submitted: Optional[bool] = None
    operation_theatre_notes_submitted: Optional[bool] = None
    ecg_submitted: Optional[bool] = None
    pharmacy_bill_submitted: Optional[bool] = None
    other_documents_submitted: Optional[bool] = None


class HospitalDetails(BaseModel):
    hospital_name: Optional[str] = None
    hospital_id: Optional[str] = None
    hospital_address: Optional[str] = None
    hospital_type: Optional[str] = None
    doctor_name: Optional[str] = None
    doctor_qualification: Optional[str] = None
    doctor_registration_no: Optional[str] = None
    diagnosis: Optional[str] = None
    procedure: Optional[str] = None
    treating_doctor: Optional[str] = None


class Diagnosis(BaseModel):
    primary_icd_code: Optional[str] = None
    primary_icd_description: Optional[str] = None
    secondary_icd_code: Optional[str] = None
    secondary_icd_description: Optional[str] = None


class Comorbidity(BaseModel):
    code: Optional[str] = None
    description: Optional[str] = None


class ProcedureCode(BaseModel):
    code: Optional[str] = None
    description: Optional[str] = None


class PreAuthorization(BaseModel):
    is_obtained: Optional[bool] = None
    approval_number: Optional[str] = None
    rejection_or_missing_reason: Optional[str] = None


class InjuryDetails(BaseModel):
    is_injury: Optional[bool] = None
    cause_type: Optional[str] = None
    alcohol_or_substance_abuse_suspected: Optional[bool] = None
    medico_legal_case: Optional[bool] = None
    police_reported: Optional[bool] = None
    fir_number: Optional[str] = None


class DiagnosisAndTreatment(BaseModel):
    diagnosis: Diagnosis = Field(default_factory=Diagnosis)
    comorbidities: List[Comorbidity] = Field(default_factory=list)
    procedures: List[ProcedureCode] = Field(default_factory=list)
    procedure_notes: Optional[str] = None
    pre_authorization: Optional[PreAuthorization] = None
    injury_details: Optional[InjuryDetails] = None


class BankDetails(BaseModel):
    beneficiary_name: Optional[str] = None
    bank_name: Optional[str] = None
    account_no: Optional[str] = None
    ifsc: Optional[str] = None


class Declaration(BaseModel):
    declaration_text: Optional[str] = None
    signature_name: Optional[str] = None
    signature_date: Optional[str] = None


class ClaimForm(BaseModel):
    primary_insured: Optional[PrimaryInsured] = None
    insurance_history: Optional[InsuranceHistory] = None
    patient_details: Optional[PatientDetails] = None
    hospitalization_details: Optional[HospitalizationDetails] = None
    claim_expenses: Optional[ClaimExpenses] = None
    benefits: Optional[BenefitDetails] = None
    document_checklist: Optional[DocumentChecklist] = None
    hospital_details: Optional[HospitalDetails] = None
    diagnosis_and_treatment: Optional[DiagnosisAndTreatment] = None
    bank_details: Optional[BankDetails] = None
    declaration: Optional[Declaration] = None


class PrescriptionMedication(BaseModel):
    name: str
    strength: str
    form: str
    dosage: str
    frequency: str
    duration_days: int
    instructions: str


class PrescriptionRecord(BaseModel):
    prescription_id: str
    date: str
    prescriber_name: str
    registration_no: str
    clinic: str
    medications: List[PrescriptionMedication]
    notes: str
    file: str


class ClaimDatabaseRecord(BaseModel):
    claim_id: str
    submitted_date: str
    insurance_claimed: bool
    claim_status: str
    claim_form: ClaimForm
    prescriptions: List[PrescriptionRecord]
    bills_details: list[dict]
    claim_documents_submitted_checklist: dict
    uploaded_files: List[str]


class PolicyRecord(BaseModel):
    policy_no: str
    tpa_id: Optional[str]
    policy_holder_name: str
    active: bool
    start_date: str
    end_date: str
    waiting_period_days: int
    sum_insured: float
    room_rent_cap_per_day: float
    co_pay_percentage: float
    exclusions: List[str]
    covered_icd_codes: List[str]
    covered_conditions: List[str]


class HospitalNetworkRecord(BaseModel):
    hospital_id: str
    hospital_name: str
    hospital_type: str
    city: str
    in_network: bool
    specialties: List[str]
    doctor_registration_numbers: List[str]
