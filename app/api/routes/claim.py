# Nedd to accept both policy doc and claim form from user
# maybe two routes -
# 1. for submitting Policy docs
# 2. for submitting Claim Form

from datetime import datetime

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.db import get_db

from app.models.claim import PolicyDocs
from app.services.policy.pipeline import ingest_policy_document
import boto3
import uuid

from app.workflows import graph

s3_client = boto3.client('s3')
BUCKET_NAME = "policy-docs-bucket"

def upload_to_s3(file_bytes: bytes, filename: str) -> str:
    """Uploads file to S3 and returns the unique storage key path."""
    # Generate a unique key name to avoid naming collisions
    unique_id = uuid.uuid4().hex
    s3_key = f"policies/{unique_id}_{filename}"
    
    s3_client.put_object(
        Bucket=BUCKET_NAME,
        Key=s3_key,
        Body=file_bytes,
        ContentType="application/pdf"
    )
    return s3_key



MAX_FILE_SIZE = 5 * 1024 * 1024
router = APIRouter()

@router.post('/policy_doc')
async def upload_policy_doc(company_id: int = Form(...),
    policy_name: str = Form(...),
    policy_code: str = Form(...),
    version: str = Form("v1"),
    policy_file:UploadFile = Form("v1"), 
    db:Session = Depends(get_db)
    ):
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
    # store the file to s3 bucket 
    # put the source from s3 bucket to the PolicyDocs table in the database
    # send the uploaded file to the pipeline 
    # 3. Save file to Cloud Object Storage
    try:
        s3_storage_path = upload_to_s3(pdf_content, policy_file.filename)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save file to storage system: {str(e)}"
        )

    # 4. Create Database Entry
    new_policy = PolicyDocs(
        company_id=company_id,
        policy_name=policy_name,
        policy_code=policy_code,
        version=version,
        source_file=s3_storage_path, # S3 location tracker
        ingested_at=datetime.now()
    )
    
    try:
        db.add(new_policy)
        db.commit()
        db.refresh(new_policy)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Database conflict. Ensure company exists and combination is unique."
        )

    # 5. Hand over to background processing pipeline
    # Recommend using a task runner like Celery or FastAPI BackgroundTasks here
    ingest_policy_document(db, new_policy.id, pdf_content)


    
    return {
        "filename": policy_file.filename,
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
    storage_path = upload_to_s3(pdf_content, policy_file.filename)

    # 3. Create the initial LangGraph state payload
    initial_state = {
        "raw_pdf_bytes": pdf_content,       # Option A: Send raw bytes directly into the graph
        "file_path": storage_path,        # Option B: Send cloud path instead
        "filename": policy_file.filename,
        "next_step": "data_extraction"     # Bootstrapping your workflow routing
    }

    # 4. Kick off the LangGraph processing workflow synchronously or asynchronously
    try:
        final_state = await graph.icca_graph.ainvoke(initial_state)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Graph execution failed during audit: {str(e)}"
        )

    # 5. Return the finalized state evaluation or a success ticket
    return {
        "filename": policy_file.filename,
        "status": "Processing complete",
        "audit_results": final_state.get("audit_report", {}),
        "decision": final_state.get("decision_status", "Unknown")
    }