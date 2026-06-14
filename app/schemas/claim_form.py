from __future__ import annotations
import enum
from typing import List, Optional

from pydantic import BaseModel
class Relationship(str, enum.Enum):
    SELF = "self"
    SPOUSE = "spouse"
    CHILD = "child"
    PARENT = "parent"

class PrimaryInsured(BaseModel):
    policy_no: Optional[str] 
    tpa_id: Optional[str] 
    policy_holder_name: str 
    address: Optional[str] 
    city: Optional[str] 
    state: Optional[str] 
    pin_code: Optional[str] 
    phone: Optional[str] 
    email: Optional[str] 


class InsuranceHistory(BaseModel):
    other_medical_insurance: Optional[bool] 
    commencement_without_break_date: Optional[str] 
    insurance_company_name: Optional[str] 
    previous_policy_no: Optional[str] 
    sum_insured: Optional[float] 
    hospitalized_in_last_four_years: Optional[bool] 


class PatientDetails(BaseModel):
    patient_name: Optional[str] 
    relationship_to_policy_holder: Relationship
    gender: Optional[str] 
    age: Optional[int] 
    date_of_birth: Optional[str] 
    occupation: Optional[str] 
    room_category: Optional[str] 
    hospitalization_reason: Optional[str] 
    system_of_medicine: Optional[str] 


class HospitalizationDetails(BaseModel):
    date_of_admission: Optional[str] 
    time_of_admission: Optional[str] 
    date_of_discharge: Optional[str] 
    time_of_discharge: Optional[str] 
    type_of_admission: Optional[str] 
    status_at_discharge: Optional[str] 


class ClaimExpenses(BaseModel):
    hospitalization_expenses: Optional[float] 
    pre_hospitalization_expenses: Optional[float] 
    pre_hospitalization_period_days: Optional[int] 
    post_hospitalization_expenses: Optional[float] 
    post_hospitalization_period_days: Optional[int] 
    health_checkup_cost: Optional[float] 
    ambulance_charges: Optional[float] 
    other_expenses: Optional[float] 
    total_expenses: Optional[float] 


class BenefitDetails(BaseModel):
    hospital_daily_cash: Optional[float] 
    surgical_cash: Optional[float] 
    critical_illness_benefit: Optional[float] 
    convalescence_benefit: Optional[float] 
    pre_post_lump_sum_benefit: Optional[float] 
    other_benefits: Optional[float] 
    total_lump_sum_benefit: Optional[float] 


class DocumentChecklist(BaseModel):
    claim_form_submitted: Optional[bool] 
    intimation_letter_submitted: Optional[bool] 
    hospital_main_bill_submitted: Optional[bool] 
    hospital_breakup_bill_submitted: Optional[bool] 
    payment_receipt_submitted: Optional[bool] 
    discharge_summary_submitted: Optional[bool] 
    doctor_prescription_submitted: Optional[bool] 
    investigation_request_submitted: Optional[bool] 
    investigation_reports_submitted: Optional[bool] 
    operation_theatre_notes_submitted: Optional[bool] 
    ecg_submitted: Optional[bool] 
    pharmacy_bill_submitted: Optional[bool] 
    other_documents_submitted: Optional[bool] 


class HospitalDetails(BaseModel):
    hospital_name: Optional[str] 
    hospital_id: Optional[str] 
    hospital_address: Optional[str] 
    hospital_type: Optional[str] 
    doctor_name: Optional[str] 
    doctor_qualification: Optional[str] 
    doctor_registration_no: Optional[str] 
    diagnosis: Optional[str] 
    procedure: Optional[str] 
    treating_doctor: Optional[str] 


class Diagnosis(BaseModel):
    primary_icd_code: Optional[str] 
    primary_icd_description: Optional[str] 
    secondary_icd_code: Optional[str] 
    secondary_icd_description: Optional[str] 


class Comorbidity(BaseModel):
    code: Optional[str] 
    description: Optional[str] 


class ProcedureCode(BaseModel):
    code: Optional[str] 
    description: Optional[str] 


class PreAuthorization(BaseModel):
    is_obtained: Optional[bool] 
    approval_number: Optional[str] 
    rejection_or_missing_reason: Optional[str] 


class InjuryDetails(BaseModel):
    is_injury: Optional[bool] 
    cause_type: Optional[str] 
    alcohol_or_substance_abuse_suspected: Optional[bool] 
    medico_legal_case: Optional[bool] 
    police_reported: Optional[bool] 
    fir_number: Optional[str] 


class BankDetails(BaseModel):
    beneficiary_name: Optional[str] 
    bank_name: Optional[str] 
    account_no: Optional[str] 
    ifsc: Optional[str] 


class Declaration(BaseModel):
    declaration_text: Optional[str] 
    signature_name: Optional[str] 
    signature_date: Optional[str] 


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


class PolicyRecord(BaseModel):
    policy_no: str
    tpa_id: Optional[str]
    policy_holder_name: str
    active: bool
    start_date: Optional[str]
    end_date: Optional[str]
    waiting_period_days: Optional[int]
    sum_insured: float
    room_rent_cap_per_day: Optional[float]
    co_pay_percentage: Optional[float]
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


class VerificationCheck(BaseModel):
    passed: bool 
    reason: Optional[str] 


class VerificationResult(BaseModel):
    user: VerificationCheck 
    policy: VerificationCheck
    patient: VerificationCheck
    documents:VerificationCheck
    overall_verified: bool 

