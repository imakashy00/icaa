from openai import OpenAI

from app.core.settings import settings


class EmbeddingService:
    """
    Singleton wrapper so the (relatively heavy) embedding model is loaded
    into memory once per process, not once per call.
    """

    _instance = None

    def __new__(cls,*args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self,'client'):
            self.client = OpenAI()

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """
        Embeds a batch of texts. Used during ingestion to embed every
        clause chunk in one pass.
        """
        if not texts: 
            return []

        response = self.client.embeddings.create(
            input=texts, model=settings.embedding_model
        )
        return [data.embedding for data in response.data]

    def embed_query(self, text: str) -> list[float]:
        """Convenience wrapper for embedding a single query string at audit time."""
        return self.embed_texts([text])[0]
