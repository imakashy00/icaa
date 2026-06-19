"""
Embedding generation, kept local (sentence-transformers) rather than via an
API: ingestion produces hundreds of embeddings per policy, and every audit
does at least one query-time embedding, so this needs to be fast and free of
per-call API cost/latency.

Swap `settings.embedding_model` for a hosted embedding API (OpenAI, Voyage,
Cohere) if you need higher retrieval quality -- just keep
`settings.embedding_dim` and the `Vector(...)` column in models.py in sync
with the new model's output dimension.
"""

from sentence_transformers import SentenceTransformer

from app.core.settings import settings


class EmbeddingService:
    """
    Singleton wrapper so the (relatively heavy) embedding model is loaded
    into memory once per process, not once per call.
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.model = SentenceTransformer(settings.embedding_model)
        return cls._instance

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """
        Embeds a batch of texts. Used during ingestion to embed every
        clause chunk in one pass.
        """
        embeddings = self.model.encode(
            texts, normalize_embeddings=True, show_progress_bar=False
        )
        return embeddings.tolist()

    def embed_query(self, text: str) -> list[float]:
        """Convenience wrapper for embedding a single query string at audit time."""
        return self.embed_texts([text])[0]
