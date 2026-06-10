from app.schemas.claim_form import (
    PrimaryInsured,
    InsuranceHistory,
    PatientDetails,
    HospitalizationDetails,
    ClaimExpenses,
    BenefitDetails,
    DocumentChecklist,
    HospitalDetails,
    Diagnosis,
    Comorbidity,
    ProcedureCode,
    PreAuthorization,
    InjuryDetails,
    DiagnosisAndTreatment,
    BankDetails,
    Declaration,
    ClaimForm,
)


DOCUMENT_CATEGORY_TO_SCHEMA = {
    "Claim Form": ClaimForm,
    "Insurance Card": PrimaryInsured,
    "Discharge Summary": HospitalizationDetails,
    "Final Hospital Bill": ClaimExpenses,
    "Lab Report": DiagnosisAndTreatment,
    "Prescription": DiagnosisAndTreatment,
    "KYC Document": PrimaryInsured,
    "Bank Document": BankDetails,
    "Insurance History": InsuranceHistory,
    "Patient Details": PatientDetails,
    "Hospital Details": HospitalDetails,
    "Diagnosis Report": Diagnosis,
    "Comorbidity Record": Comorbidity,
    "Procedure Code Log": ProcedureCode,
    "Pre Authorization Letter": PreAuthorization,
    "Injury Details": InjuryDetails,
    "Benefit Details": BenefitDetails,
    "Document Checklist": DocumentChecklist,
    "Declaration Form": Declaration,
    "Unknown": None,
}


def normalize_category(category: str) -> str:
    return " ".join(category.strip().split())

CATEGORY_TO_SCHEMA = {
    "PrimaryInsured": PrimaryInsured,
    "InsuranceHistory": InsuranceHistory,
    "PatientDetails": PatientDetails,
    "HospitalizationDetails": HospitalizationDetails,
    "ClaimExpenses": ClaimExpenses,
    "BenefitDetails": BenefitDetails,
    "DocumentChecklist": DocumentChecklist,
    "HospitalDetails": HospitalDetails,
    "Diagnosis": Diagnosis,
    "Comorbidity": Comorbidity,
    "ProcedureCode": ProcedureCode,
    "PreAuthorization": PreAuthorization,
    "InjuryDetails": InjuryDetails,
    "DiagnosisAndTreatment": DiagnosisAndTreatment,
    "BankDetails": BankDetails,
    "Declaration": Declaration,
    "ClaimForm": ClaimForm,
}

CLAIM_FORM_SCHEMA = ClaimForm
