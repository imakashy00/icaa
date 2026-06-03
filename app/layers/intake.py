# Purpose: Receives files, standardizes file formats (PDF, JPEG, HEIC), 
# generates the unique claim_id, and initialises your ClaimState.
# Suggestion: Implement a validation check for file corruption and basic image quality right here. 
# If an image is too blurry, reject it immediately to save LLM token costs in the extraction layer.

import cv2
import os
from PIL import Image, ImageFile
from pypdf import PdfReader

# Configure Pillow to catch truncated/broken images during pixel operations
ImageFile.LOAD_TRUNCATED_IMAGES = False

def check_image_quality(image_path: str, threshold: float = 100.0) -> bool:
    """
    Computes the Laplacian variance to detect if an image is blurry.
    A lower variance means the image lacks sharp edges (blurry).
    """
    # Load the image in grayscale
    image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    
    if image is None:
        raise ValueError("Could not open or read the image file.")
        
    # Calculate the Laplacian variance
    variance = cv2.Laplacian(image, cv2.CV_64F).var()
    
    # If variance is below the threshold, the image is too blurry
    return variance >= threshold



def is_valid_pdf(file_path: str) -> bool:
    """
    Checks if a PDF has a valid EOF marker and can be opened/parsed structurally.
    """
    try:
        # Check 1: Quick binary check for the EOF (End of File) standard marker
        with open(file_path, "rb") as f:
            f.seek(-1024, os.SEEK_END)  # Look at the last kilobyte of the file
            last_bytes = f.read()
            if b"%%EOF" not in last_bytes:
                return False
        
        # Check 2: Structural integrity check (attempts to read pages)
        reader = PdfReader(file_path)
        _ = len(reader.pages)  # Accessing pages forces a parsing check
        return True
        
    except Exception:
        # Catching file errors, encryption issues, or malformed data streams
        return False


def is_valid_image(file_path: str) -> bool:
    """
    Attempts to read the pixel buffer of an image to verify it isn't corrupted.
    """
    try:
        with Image.open(file_path) as img:
            # Check 1: Verify the file format is recognized
            img.verify()  
            
        # Check 2: Deep pixel check (verify works superficially; load() actually parses pixels)
        with Image.open(file_path) as img:
            img.load()  # This will fail if internal pixel blocks are corrupted
            
        return True
    except Exception:
        return False


# --- Example Integration into your Claim Workflow ---
def run_intake_integrity_check(file_path: str) -> dict:
    """
    Evaluates the file and formats the response for your ClaimState.
    """
    _, ext = os.path.splitext(file_path).lower()
    
    if ext == ".pdf":
        is_valid = is_valid_pdf(file_path)
    elif ext in [".jpg", ".jpeg", ".png", ".heic"]:
        is_valid = is_valid_image(file_path)
    else:
        return {"status": "Rejected", "reason": f"Unsupported file type: {ext}"}
        
    if not is_valid:
        return {
            "status": "Rejected",
            "reason": "File corrupted during upload. Cannot parse data structure."
        }
        
    return {"status": "Valid", "reason": "File integrity verified."}
