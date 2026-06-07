from typing import Any


async def document_classifier_node(state: Any):
    # Lazy-import to avoid requiring OPENAI_API_KEY at module import time
    from app.core.settings import settings
    from app.services.policy.document_classification import DocumentClassifierAgent

    api_key = getattr(settings, "OPENAI_API_KEY", None)
    if not api_key:
        # If an API key is not present, skip classification and end the subgraph
        return {
            "classified_documents": {},
            "current_agent": "DocumentClassifier",
            "next_step": "completed",
        }

    classifier = DocumentClassifierAgent(api_key=api_key)
    document_texts = state.get("document_texts", {})
    results = await classifier.classify_documents(document_texts)
    return {
        "classified_documents": results,
        "current_agent": "DocumentClassifier",
        "next_step": "document_extraction",
    }
