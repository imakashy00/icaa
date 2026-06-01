from app.core.settings import settings
from app.graph.orchestrator import ClaimState
from app.tools.document_classification import DocumentClassifierAgent


classifier = DocumentClassifierAgent(api_key=settings.OPENAI_API_KEY)


async def document_classifier_node(state: ClaimState):

    results = await classifier.classify_documents(state["document_texts"])

    return {
        "classified_documents": results,
        "current_agent": "DocumentClassifier",
        "next_step": "document_extraction",
    }
