# Nedd to accept both policy doc and claim form from user
# maybe two routes -
# 1. for submitting Policy docs
# 2. for submitting Claim Form

from datetime import datetime
import os
from pathlib import Path

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
    status,
)
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.db import get_db

from app.models.claim import Company, PolicyDocument
from app.services.policy.pipeline import ingest_policy_document
from app.workflows.initial_data import INITIAL_STATE
import boto3
import uuid

from app.workflows.graph import icaa_graph
from app.workflows.state import ClaimState

s3_client = boto3.client("s3")
BUCKET_NAME = "policy-docs-bucket"


class PolicyDocRequest(BaseModel):
    policy_name: str
    policy_code: str
    version: str
    policy_file: UploadFile

    @classmethod
    def as_form(
        cls,
        policy_name: str = Form(...),
        policy_code: str = Form(...),
        version: str = Form("v1"),
        policy_file: UploadFile = Form(...),
    ) -> "PolicyDocRequest":
        return cls(
            policy_name=policy_name,
            policy_code=policy_code,
            version=version,
            policy_file=policy_file,
        )


# Create a local mock storage directory
# Navigates up 4 levels: claim.py -> routes -> api -> app -> icaa
PROJECT_ROOT = Path(__file__).resolve().parents[3]
MOCK_STORAGE_DIR = PROJECT_ROOT / "./mock_s3_storage"
MOCK_STORAGE_DIR.mkdir(parents=True, exist_ok=True)


def upload_to_s3(file_bytes: bytes, filename: str) :
    """Mocks S3 upload by saving the file locally on your machine."""
    unique_id = uuid.uuid4().hex
    s3_key = f"policies/{unique_id}_{filename}"
    # Simulate saving to disk
    local_path = os.path.join(MOCK_STORAGE_DIR, f"{unique_id}_{filename}")
    with open(local_path, "wb") as f:
        f.write(file_bytes)

    # Return the exact same key format so your DB logic remains unchanged
    return s3_key, local_path


# def upload_to_s3(file_bytes: bytes, filename: str) -> str:
#     """Uploads file to S3 and returns the unique storage key path."""
#     # Generate a unique key name to avoid naming collisions
#     unique_id = uuid.uuid4().hex
#     s3_key = f"policies/{unique_id}_{filename}"

#     s3_client.put_object(
#         Bucket=BUCKET_NAME, Key=s3_key, Body=file_bytes, ContentType="application/pdf"
#     )
#     return s3_key


MAX_FILE_SIZE = 5 * 1024 * 1024
router = APIRouter()

CURRENT_DIR = Path(__file__).parent


@router.get("/", response_class=HTMLResponse)
async def serve_upload_page():
    html_file_path = CURRENT_DIR / "home.html"
    html_content = html_file_path.read_text(encoding="utf-8")
    return HTMLResponse(content=html_content)


@router.post("/policy_doc")
async def upload_policy_doc(
    form_data: PolicyDocRequest = Depends(PolicyDocRequest.as_form),
    db: Session = Depends(get_db),
):
    filename = form_data.policy_file.filename
    if not filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded file must have a valid filename.",
        )
    if form_data.policy_file.content_type != "application/pdf":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Only PDF files are allowed.",
        )
    pdf_content = await form_data.policy_file.read()
    if len(pdf_content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File is too large. Maximum allowed size is 5MB.",
        )
    try:
        company = (
            db.query(Company).filter(Company.name == form_data.policy_name).first()
        )

        if not company:
            # If Company.id is set up with a uuid4 default in SQLAlchemy,
            company = Company(name=form_data.policy_name)
            db.add(company)
            db.flush() # using flush instead of commit to reserve the id without locking the transaction permanantly

        # Extract the resolved company ID
        resolved_company_id = company.id
        s3_storage_path, absolute_local_path = upload_to_s3(pdf_content, filename)
    
    # 5. Hand over to background processing pipeline
    # Recommend using a task runner like Celery or FastAPI BackgroundTasks here
        policy_id = ingest_policy_document(
            db,
            absolute_local_path,
            resolved_company_id,
            form_data.policy_name,
            form_data.policy_code,
            form_data.version,
        )
        # Optional: If you want to keep the final stored asset pointer as the S3 path in DB,
        # update it right before committing
        policy_record = db.query(PolicyDocument).get(policy_id)
        if policy_record:
            policy_record.source_file = s3_storage_path

        db.commit()
    except Exception as e:
        db.rollback()  # Wipes out the Company and Policy metadata if PyMuPDF or database crashes
        print(f"Ingestion crashed, rolling back transaction: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to process and upload policy document: {str(e)}",
        )

    return {
        "filename": filename,
        "policy_id": policy_id,
        "status": "Successfully uploaded",
    }


@router.post("/claim_doc")
async def upload_policy_claim_doc(policy_file: UploadFile = File(...)):
    if policy_file.content_type != "application/pdf":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Only PDF files are allowed.",
        )
    pdf_content = await policy_file.read()
    if len(pdf_content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File is too large. Maximum allowed size is 5MB.",
        )
    filename = policy_file.filename
    if not filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded file must have a valid filename.",
        )
    storage_path = upload_to_s3(pdf_content, filename)

    # 3. Kick off the LangGraph processing workflow synchronously or asynchronously
    try:
        final_state = await icaa_graph.ainvoke(ClaimState.model_validate(INITIAL_STATE))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Graph execution failed during audit: {str(e)}",
        )

    # 4. Return the finalized state evaluation or a success ticket
    return {
        "filename": policy_file.filename,
        "status": "Processing complete",
        "audit_results": final_state.get("audit_report", {}),
        "decision": final_state.get("decision_status", "Unknown"),
    }
