"""Base de conhecimento (RAG): indexação incremental no Chroma e busca com limiar."""

import hashlib

import chromadb

from config import CHROMA_DIR, CHUNK_OVERLAP, CHUNK_SIZE, DOCS_DIR, DOCS_TOP_K, MIN_DOC_SCORE
from embeddings import embed

_client = chromadb.PersistentClient(path=str(CHROMA_DIR))
docs_collection = _client.get_or_create_collection("docs", metadata={"hnsw:space": "cosine"})


def load_documents() -> list[dict[str, str]]:
    return [
        {"source": path.name, "text": path.read_text(encoding="utf-8")}
        for path in sorted(DOCS_DIR.glob("*"))
        if path.suffix in {".md", ".txt"}
    ]


def split_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Divide respeitando parágrafos; parágrafos longos são cortados com sobreposição."""
    chunks: list[str] = []
    current = ""
    for paragraph in (p.strip() for p in text.split("\n\n")):
        if not paragraph:
            continue
        if current and len(current) + len(paragraph) + 2 <= chunk_size:
            current += "\n\n" + paragraph
            continue
        if current:
            chunks.append(current)
        while len(paragraph) > chunk_size:
            chunks.append(paragraph[:chunk_size])
            paragraph = paragraph[chunk_size - overlap :]
        current = paragraph
    if current:
        chunks.append(current)
    return chunks


def sync_index() -> str:
    """Deixa o índice igual à pasta de docs: reindexa o que mudou, remove o que sumiu."""
    documents = load_documents()
    indexed = docs_collection.get(include=["metadatas"])
    indexed_hashes = {m["source"]: m["hash"] for m in indexed["metadatas"] or []}

    for source in set(indexed_hashes) - {d["source"] for d in documents}:
        docs_collection.delete(where={"source": source})

    reindexed = []
    for document in documents:
        digest = hashlib.sha256(
            f"{CHUNK_SIZE}:{CHUNK_OVERLAP}:{document['text']}".encode()
        ).hexdigest()
        if indexed_hashes.get(document["source"]) == digest:
            continue
        docs_collection.delete(where={"source": document["source"]})
        chunks = split_text(document["text"])
        docs_collection.add(
            ids=[f"{document['source']}#{n}" for n in range(len(chunks))],
            documents=chunks,
            embeddings=embed(chunks),
            metadatas=[
                {"source": document["source"], "chunk": n, "hash": digest}
                for n in range(len(chunks))
            ],
        )
        reindexed.append(document["source"])
    return f"{docs_collection.count()} chunks indexados (reindexados agora: {reindexed or 'nenhum'})"


def search_docs(query: str) -> list[tuple[str, float, str]]:
    """(id, score, texto) dos chunks relevantes, já filtrados pelo limiar."""
    result = docs_collection.query(
        query_embeddings=embed([query]), n_results=DOCS_TOP_K, include=["documents", "distances"]
    )
    hits = [
        (chunk_id, 1 - distance, text)
        for chunk_id, distance, text in zip(
            result["ids"][0], result["distances"][0], result["documents"][0]
        )
    ]
    return [hit for hit in hits if hit[1] >= MIN_DOC_SCORE]
