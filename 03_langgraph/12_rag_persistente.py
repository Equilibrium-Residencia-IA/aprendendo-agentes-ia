"""Décimo segundo passo: RAG com índice persistente no Chroma.

Diferenças em relação ao 11:
- os chunks ficam em disco (pasta chroma_db) e sobrevivem entre execuções;
- a indexação é sincronizada: só roda de novo o que mudou nos arquivos;
- search_docs consulta o Chroma em vez do InMemoryStore.
Reaproveita do 08 o embedding, o modelo e as tools de memória; do 09 o carregamento
e o split; do 11 o prompt, o TOP_K e o limiar.
"""

import hashlib
from importlib import import_module
from pathlib import Path

import chromadb
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import START, StateGraph
from langgraph.prebuilt import ToolNode

passo_08 = import_module("08_busca_semantica")
passo_09 = import_module("09_documentos")
passo_11 = import_module("11_rag_citacoes")

CHROMA_DIR = Path(__file__).with_name("chroma_db")
COLLECTION_NAME = "docs"


def get_collection(client: chromadb.ClientAPI) -> chromadb.Collection:
    """Coleção com distância de cosseno (nossos vetores já são normalizados)."""
    return client.get_or_create_collection(COLLECTION_NAME, metadata={"hnsw:space": "cosine"})


def sync_index(
    collection: chromadb.Collection,
    documents: list[dict[str, str]],
    chunk_size: int = passo_09.CHUNK_SIZE,
    overlap: int = passo_09.CHUNK_OVERLAP,
) -> str:
    """Deixa o índice igual aos arquivos: reindexa o que mudou e remove o que sumiu."""
    current_sources = {document["source"] for document in documents}
    indexed = collection.get(include=["metadatas"])
    indexed_hashes = {
        meta["source"]: meta["hash"] for meta in indexed["metadatas"] or []
    }

    # Arquivos apagados da pasta saem do índice.
    for source in set(indexed_hashes) - current_sources:
        collection.delete(where={"source": source})

    reindexed = []
    for document in documents:
        # O hash inclui os parâmetros do split: mudar o chunk_size também reindexa.
        digest = hashlib.sha256(f"{chunk_size}:{overlap}:{document['text']}".encode()).hexdigest()
        if indexed_hashes.get(document["source"]) == digest:
            continue
        collection.delete(where={"source": document["source"]})
        chunks = passo_09.split_text(document["text"], chunk_size, overlap)
        collection.add(
            ids=[f"{document['source']}#{n}" for n in range(len(chunks))],
            documents=chunks,
            embeddings=passo_08.embed(chunks),
            metadatas=[
                {"source": document["source"], "chunk": n, "hash": digest}
                for n in range(len(chunks))
            ],
        )
        reindexed.append(document["source"])

    return f"{collection.count()} chunks no índice; reindexados: {reindexed or 'nenhum'}"


def search(collection: chromadb.Collection, query: str, top_k: int) -> list[tuple[str, float, str]]:
    """Retorna (id, score, texto). O Chroma devolve distância; score = 1 - distância."""
    result = collection.query(
        query_embeddings=passo_08.embed([query]),
        n_results=top_k,
        include=["documents", "distances"],
    )
    return [
        (chunk_id, 1 - distance, text)
        for chunk_id, distance, text in zip(
            result["ids"][0], result["distances"][0], result["documents"][0]
        )
    ]


client = chromadb.PersistentClient(path=str(CHROMA_DIR))
collection = get_collection(client)


@tool
def search_docs(query: str) -> str:
    """Busca nos documentos da loja trechos relacionados à pergunta."""
    relevant = [
        hit for hit in search(collection, query, passo_11.TOP_K) if hit[1] >= passo_11.MIN_DOC_SCORE
    ]
    if not relevant:
        return "Nenhum trecho relevante encontrado nos documentos."
    return "\n\n".join(f"[{chunk_id}] (score {score:.2f})\n{text}" for chunk_id, score, text in relevant)


tools = [search_docs, passo_08.save_memory, passo_08.retrieve_memory]
model_with_tools = passo_08.model.bind_tools(tools)


def call_model(state: passo_08.AgentState) -> dict:
    messages = [SystemMessage(content=passo_11.SYSTEM_PROMPT), *state["messages"]]
    return {"messages": [model_with_tools.invoke(messages)]}


workflow = StateGraph(passo_08.AgentState)
workflow.add_node("call_model", call_model)
workflow.add_node("tools", ToolNode(tools))
workflow.add_edge(START, "call_model")
workflow.add_conditional_edges("call_model", passo_08.should_continue)
workflow.add_edge("tools", "call_model")
# A memória do usuário continua no store do 08; só os documentos foram para o Chroma.
agent = workflow.compile(checkpointer=InMemorySaver(), store=passo_08.store)


def run_chat() -> None:
    user_id = "usuario-local"
    passo_08.seed_memories(user_id)
    print(sync_index(collection, passo_09.load_documents(passo_09.DOCS_DIR)), "\n")

    config: RunnableConfig = {"configurable": {"thread_id": "conversa-rag"}}
    while True:
        user_input = input("Input: ").strip()
        if not user_input:
            print("Encerrando a conversa.")
            return
        result = agent.invoke(
            {"messages": [HumanMessage(content=user_input)], "user_id": user_id}, config
        )
        print(result["messages"][-1].content, "\n")


if __name__ == "__main__":
    run_chat()
