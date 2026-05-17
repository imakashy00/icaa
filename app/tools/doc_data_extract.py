import io
import openai
import base64
import pymupdf4llm
from pydantic import BaseModel, Field
from typing import List, Optional,Any
from openai.types.chat import ChatCompletionUserMessageParam

class Prescription(BaseModel):
    doctor_name:str
    hospital_clicnic:Optional[str]
    medications:List[str] = Field(description='Name, Dosage and Frequency')

class InsuranceCard(BaseModel):
    carrier_name:str
    policy_number:str
    group_number:Optional[str]
    subscriber_name:str

class LabReport(BaseModel):
    laboratory_name:str
    test_date:str
    abnormal_findings: List[str] = Field(description="List out any values flagged as high, low, or out of range")

class Identity(BaseModel):
    pass
class MedicalFields(BaseModel):
    pass
class FinancialFields(BaseModel):
    pass
class SupportingDocs(BaseModel):
    pass
class BankDetails(BaseModel):
    pass

class ClaimForm(BaseModel):
    identity:Identity
    medical_filelds:MedicalFields
    financial_fields:FinancialFields
    supporting_docs:SupportingDocs
    bank_details:BankDetails


class DischargeSummary(BaseModel):
    pass

class HospitalBill(BaseModel):
    pass


EXTRACTION_REGISTRY = {
    "Prescription":Prescription,
    "InsuranceCard":InsuranceCard,
    "LabReport":LabReport,
    "ClaimForm":ClaimForm,
    "DischargeSummary":DischargeSummary,
    "HospitalBill":HospitalBill,
}

def extract_markdown_from_pdf(file_bytes:bytes):
    pdf_stream = io.BytesIO(file_bytes)
    return pymupdf4llm.to_markdown(pdf_stream)
    

def extract_pdf_data(category:str,file_bytes:bytes,target_schema:Any):

    client = openai.OpenAI(api_key='sjflsjdfljsldfk')
    extracted_markdown = extract_markdown_from_pdf(file_bytes)
    if not extracted_markdown:
        raise ValueError("Pdf contains no readable content or text layers")
    
    messages = [
        {
            "role": "system",
            "content": (
                f"You are an expert data parser. Extract structured details from the following "
                f"raw {category} text. The text is formatted in Markdown, and tabular data is "
                f"represented as Markdown tables. Parse them carefully."
            )
        },
        {
            "role": "user",
            "content": extracted_markdown,
        }
    ]
    response = client.chat.completions.parse(
        model='gpt-4o-mini',
        messages=messages,
        response_format=target_schema,
    )
    return response.choices[0].message.parsed

def extract_image_data(category:str,file_bytes:bytes,taraget_schema:Any):
    base64_image = base64.b64encode(file_bytes).decode('utf-8')
    client = openai.OpenAI(api_key='sakfhsadfmsdkfhsdkfh')
    messages: list[ChatCompletionUserMessageParam] = [
            {
                "role": "user",
                "content":[
                    {
                        "type": "text",
                        "text": "Extract structured data",
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{base64_image}"
                        },
                    },
                ],
            }
        ]
    response = client.chat.completions.parse(
        model='gpt-4o-mini',
        messages=messages,
        response_format=taraget_schema
    )
    return response.choices[0].message.parsed

def process_document_extraction(category: str, file_bytes: bytes, file_extension: str):
    target_schema = EXTRACTION_REGISTRY.get(category)
    if not target_schema:
        raise ValueError(f"No Schema registered for {category}")
    extension = file_extension.lower().strip('.')
    if extension =='pdf':
        return extract_pdf_data(category,file_bytes,target_schema)
    elif extension in ['jpeg', 'jpg' ,'png','webp']:
        return extract_image_data(category,file_bytes,target_schema)
    else:
        raise ValueError(f"Format .{extension} is not supported.")
    

def universal_pdf_pipeline(category: str, file_bytes: bytes, target_schema: Any):
    # Try server-side text extraction first
    text = str(extract_markdown_from_pdf(file_bytes))
    
    if text.strip():
        # It's a digital PDF -> Run the fast, ultra-cheap text endpoint
        return extract_pdf_data(category, file_bytes, target_schema)
    else:
        # It's a scanned PDF/Image -> Fall back to your Vision-based function
        print("Scanned PDF detected. Falling back to Vision Processing...")
        # (Optional: Convert page 1 to image bytes using pdf2image, then call extract_content_from_image)
