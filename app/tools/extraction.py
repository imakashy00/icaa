from app.services.claims.extraction import ExtractionAgent
from app.workflows.state import ClaimState

from app.schemas.registry import (
    CATEGORY_TO_SCHEMA,
    DOCUMENT_CATEGORY_TO_SCHEMA,
    normalize_category,
)


async def extraction_node(state: ClaimState):
    extractor = ExtractionAgent()

    extracted_documents = {}
    extraction_errors = []

    classified_documents = state.get("classified_documents", {})

    document_texts = state.get("document_texts", {})

    for file_name, classification in classified_documents.items():
        category = normalize_category(classification.get("category", "Unknown"))

        if category == "Unknown":
            extraction_errors.append(f"{file_name}: Unknown document type")
            continue

        schema = DOCUMENT_CATEGORY_TO_SCHEMA.get(category) or CATEGORY_TO_SCHEMA.get(
            category
        )

        if not schema:
            extraction_errors.append(f"{file_name}: No schema found for {category}")
            continue

        document_text = document_texts.get(file_name)

        if not document_text:
            extraction_errors.append(f"{file_name}: Missing OCR text")
            continue

        try:
            raw_extracted = await extractor.extract(
                schema=schema,
                documents_text=document_text,
            )
            extracted = schema.model_validate(raw_extracted)

            extracted_documents[file_name] = {
                "document_type": category,
                "data": extracted.model_dump(),
            }

        except Exception as e:
            extraction_errors.append(f"{file_name}: {str(e)}")

    return {
        "extracted_documents": extracted_documents,
        "extraction_errors": extraction_errors,
        "current_agent": "ExtractionAgent",
        "next_step": "claim_aggregation",
    }
