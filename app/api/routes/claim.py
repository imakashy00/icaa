# Nedd to accept both policy doc and claim form from user
# maybe two routes -
# 1. for submitting Policy docs
# 2. for submitting Claim Form

from fastapi import APIRouter, File, HTTPException, UploadFile, status

MAX_FILE_SIZE = 5 * 1024 * 1024
router = APIRouter()

@router.get('/policy_doc')
async def get_policy_doc(policy_file:UploadFile = File(...)):
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
    return {
        "filename": policy_file.filename,
        "status": "Successfully uploaded",
    }

@router.get("/policy_doc")
async def get_policy_claim(policy_file: UploadFile = File(...)):
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
    return {
        "filename": policy_file.filename,
        "status": "Successfully uploaded",
    }