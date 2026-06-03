from typing import List, Optional

from pydantic import BaseModel

from app.schemas.claim_form import (
    BankDetails,
    BenefitDetails,
    ClaimExpenses,
    ClaimForm,
    Declaration,
    Diagnosis,
    DiagnosisAndTreatment,
    DocumentChecklist,
    HospitalDetails,
    HospitalizationDetails,
    InjuryDetails,
    InsuranceHistory,
    PatientDetails,
    PreAuthorization,
    PrimaryInsured,
    ProcedureCode,
    Comorbidity,
)


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


claim_form_db = ClaimForm(
    primary_insured=PrimaryInsured(
        policy_no="POL-99887766",
        tpa_id="TPA-4521",
        policy_holder_name="Ram Yadav",
        address="Flat 12, Sunrise Apartments, MG Road",
        city="Bangalore",
        state="Karnataka",
        pin_code="560001",
        email="ram.yadav@gmail.com",
    ),
    insurance_history=InsuranceHistory(
        other_medical_insurance=True,
        commencement_without_break_date="2020-10-10",
        insurance_company_name="Star Health",
        previous_policy_no="POL-88997766",
        sum_insured=1000000,
        hospitalized_in_last_four_years=True,
    ),
    patient_details=PatientDetails(
        patient_name="Sita Yadav",
        relationship_to_policy_holder="Spouse",
        room_category="single_occupency",
        hospitalization_reason="illness",
        system_of_medicine="allopathy",
    ),
    hospitalization_details=HospitalizationDetails(
        date_of_admission="2026-05-20",
        time_of_admission="12:40PM",
        date_of_discharge="2026-05-24",
        time_of_discharge="02:45PM",
        type_of_admission="emergency",
        status_at_discharge="discharged_to_home",
    ),
    claim_expenses=ClaimExpenses(
        hospitalization_expenses=50000,
        pre_hospitalization_expenses=10200,
        pre_hospitalization_period_days=2,
        post_hospitalization_expenses=5000,
        post_hospitalization_period_days=1,
        health_checkup_cost=4040,
        ambulance_charges=6700,
        other_expenses=0,
        total_expenses=71940,
    ),
    benefits=BenefitDetails(
        hospital_daily_cash=0,
        surgical_cash=0,
        critical_illness_benefit=0,
        convalescence_benefit=0,
        pre_post_lump_sum_benefit=0,
        other_benefits=0,
        total_lump_sum_benefit=0,
    ),
    document_checklist=DocumentChecklist(
        claim_form_submitted=True,
        intimation_letter_submitted=True,
        hospital_main_bill_submitted=True,
        hospital_breakup_bill_submitted=True,
        payment_receipt_submitted=True,
        discharge_summary_submitted=True,
        doctor_prescription_submitted=True,
        investigation_request_submitted=True,
        investigation_reports_submitted=True,
        operation_theatre_notes_submitted=True,
        ecg_submitted=True,
        pharmacy_bill_submitted=True,
        other_documents_submitted=True,
    ),
    hospital_details=HospitalDetails(
        hospital_name="Green Valley Hospital",
        hospital_id="HED-MUM-HOS-0421",
        hospital_address="12 Health Park, Sector 5, Bangalore",
        hospital_type="network",
        doctor_name="Jhatka Vaid",
        doctor_qualification="MD",
        doctor_registration_no="MCI/12-45678",
        diagnosis="Acute appendicitis",
        procedure="Laparoscopic appendectomy",
        treating_doctor="Dr. S. Mehta",
    ),
    diagnosis_and_treatment=DiagnosisAndTreatment(
        diagnosis=Diagnosis(
            primary_icd_code="I21.1",
            primary_icd_description="Acute transmural myocardial infarction of inferior wall",
            secondary_icd_code="I10",
            secondary_icd_description="Essential (primary) hypertension",
        ),
        comorbidities=[
            Comorbidity(code="E11.9", description="Type 2 diabetes mellitus")
        ],
        procedures=[
            ProcedureCode(
                code="02713ZZ",
                description="Coronary Artery Dilation with Drug-Eluting Stent",
            )
        ],
        procedure_notes="Emergency Coronary Angiography followed by Primary PTCA to the Right Coronary Artery.",
        pre_authorization=PreAuthorization(
            is_obtained=False,
            approval_number=None,
            rejection_or_missing_reason="Emergency admission requiring immediate life-saving surgery. Pre-auth timeline skipped to prioritize patient care.",
        ),
        injury_details=InjuryDetails(
            is_injury=False,
            cause_type=None,
            alcohol_or_substance_abuse_suspected=False,
            medico_legal_case=False,
            police_reported=False,
            fir_number=None,
        ),
    ),
    bank_details=BankDetails(
        beneficiary_name="Sita Yadav",
        bank_name="ICICI Bank",
        account_no="987654321098",
        ifsc="ICIC0000456",
    ),
    declaration=Declaration(
        declaration_text="I hereby declare that the information provided is true to the best of my knowledge and the attached documents are authentic.",
        signature_name="Ram Yadav",
        signature_date="2026-05-25",
    ),
)

claim_db = ClaimDatabaseRecord(
    claim_id="CLM-2026-000123",
    submitted_date="2026-05-25",
    insurance_claimed=True,
    claim_status="submitted",
    claim_form=claim_form_db,
    prescriptions=[
        PrescriptionRecord(
            prescription_id="RX-2026-0001",
            date="2026-05-19",
            prescriber_name="Dr. S. Mehta",
            registration_no="MCI/12-45678",
            clinic="Green Valley Hospital",
            medications=[
                PrescriptionMedication(
                    name="Cefuroxime",
                    strength="500 mg",
                    form="tablet",
                    dosage="1 tablet",
                    frequency="twice a day",
                    duration_days=5,
                    instructions="after food",
                ),
                PrescriptionMedication(
                    name="Paracetamol",
                    strength="500 mg",
                    form="tablet",
                    dosage="1 tablet",
                    frequency="as needed",
                    duration_days=3,
                    instructions="",
                ),
            ],
            notes="Complete antibiotic course",
            file="prescription_20260519.pdf",
        )
    ],
    bills_details=[
        {
            "bill_no": "BL-2026-8942",
            "date": "15/05/2026",
            "issued_by": "Apollo Diagnostics",
            "towards": "Pre-Hospitalization: Blood tests & CT Scan",
            "amount_rs": 6500,
        },
        {
            "bill_no": "IP-77301-B",
            "date": "20/05/2026",
            "issued_by": "Max Super Specialty",
            "towards": "Hospitalization: Room rent & Surgery",
            "amount_rs": 145000,
        },
        {
            "bill_no": "PH-99214",
            "date": "22/05/2026",
            "issued_by": "Wellness Pharmacy",
            "towards": "Post-Hospitalization: Discharge Medicines",
            "amount_rs": 3200,
        },
    ],
    claim_documents_submitted_checklist={
        "forms_and_authorizations": {
            "claim_form_filled_and_signed": True,
            "original_pre_authorization_request": False,
            "copy_of_pre_authorization_approval_letter": False,
            "copy_of_patient_photo_id_verified_by_hospital": True,
        },
        "hospital_medical_records": {
            "hospital_discharge_summary": True,
            "operation_theatre_notes": True,
            "investigation_reports": True,
            "ct_mri_usg_hpe_investigation_reports": False,
            "doctors_reference_slip_for_investigation": True,
            "ecg": True,
            "original_death_summary": False,
        },
        "bills_and_financials": {
            "hospital_main_bill": True,
            "hospital_break_up_bill": True,
            "pharmacy_bills": True,
        },
        "legal_and_accident_records": {
            "mlc_report_and_police_fir": False,
        },
        "other_documents": [
            {"document_name": "Cancelled Cheque for NEFT Payout", "is_submitted": True},
            {"document_name": "Aadhaar Card of Primary Insured", "is_submitted": True},
        ],
    },
    uploaded_files=[
        "policy_document_policy_99887766.pdf",
        "hospital_bill_20260521.pdf",
        "discharge_summary_20260524.pdf",
        "patient_id_asha_kumari.jpg",
        "prescription_20260519.pdf",
    ],
)

# Backwards-compatible alias for existing imports.
user_db = claim_db
