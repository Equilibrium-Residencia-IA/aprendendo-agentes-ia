"""Memória de longo prazo por usuário, persistida no Chroma e buscada por significado.

Diferente de só expor uma tool: o grafo chama `recall` a cada turno e injeta no prompt
o que for relevante, então o agente "lembra" sem depender de o modelo decidir buscar.
"""

from datetime import datetime
from uuid import uuid4

import chromadb

from config import (
    CHROMA_DIR,
    MEMORY_TOP_K,
    MEMORY_DUPLICATE_SCORE,
    MEMORY_RELATED_SCORE,
    MIN_MEMORY_SCORE,
)
from embeddings import embed

_client = chromadb.PersistentClient(path=str(CHROMA_DIR))
memories = _client.get_or_create_collection("memories", metadata={"hnsw:space": "cosine"})


def _search(user_id: str, query: str, limit: int) -> list[tuple[str, float, str]]:
    if not memories.count():
        return []
    result = memories.query(
        query_embeddings=embed([query]),
        n_results=limit,
        where={"user_id": user_id},
        include=["documents", "distances"],
    )
    return [
        (memory_id, 1 - distance, text)
        for memory_id, distance, text in zip(
            result["ids"][0], result["distances"][0], result["documents"][0]
        )
    ]


def recall(user_id: str, query: str) -> list[str]:
    """Memórias do usuário relevantes para a consulta."""
    return [
        text
        for _, score, text in _search(user_id, query, MEMORY_TOP_K)
        if score >= MIN_MEMORY_SCORE
    ]


def remember(user_id: str, content: str) -> str:
    """Salva um fato; descarta duplicatas e lista fatos parecidos que podem ter ficado obsoletos."""
    content = content.strip()
    if not content:
        raise ValueError("A memória não pode estar vazia.")

    related = [hit for hit in _search(user_id, content, 3) if hit[1] >= MEMORY_RELATED_SCORE]
    if related and related[0][1] >= MEMORY_DUPLICATE_SCORE:
        return "Essa memória já estava salva."

    memories.add(
        ids=[str(uuid4())],
        documents=[content],
        embeddings=embed([content]),
        metadatas=[{"user_id": user_id, "created_at": datetime.now().isoformat(timespec="seconds")}],
    )
    message = "Memória salva."
    if related:
        similar = "\n".join(f"- [{memory_id[:8]}] {text}" for memory_id, _, text in related)
        message += (
            "\nJá existiam memórias parecidas. Se alguma contradiz a nova ou ficou obsoleta, "
            f"remova com forget_memory:\n{similar}"
        )
    return message


def forget(user_id: str, memory_id: str) -> str:
    """Apaga uma memória do usuário pelo prefixo do id mostrado em remember()."""
    stored = memories.get(where={"user_id": user_id})
    matches = [i for i in stored["ids"] if i.startswith(memory_id.strip("[] "))]
    if len(matches) != 1:
        return "Memória não encontrada."
    memories.delete(ids=matches)
    return "Memória removida."


def list_memories(user_id: str) -> list[str]:
    return memories.get(where={"user_id": user_id}, include=["documents"])["documents"] or []
