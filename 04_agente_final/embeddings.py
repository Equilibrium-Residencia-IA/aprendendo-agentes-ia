"""Modelo de embeddings local, carregado uma vez e compartilhado por RAG e memória."""

from sentence_transformers import SentenceTransformer

from config import EMBEDDING_MODEL

_model = SentenceTransformer(EMBEDDING_MODEL)


def embed(texts: list[str]) -> list[list[float]]:
    """Vetores normalizados: o produto escalar equivale à similaridade de cosseno."""
    return _model.encode(texts, normalize_embeddings=True).tolist()
