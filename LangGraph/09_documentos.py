"""Nono passo: carregar documentos, dividir em chunks e indexar (ingestão do RAG).

Reaproveita do passo 08 a função de embedding. Como o nome do arquivo começa com
número, o import é feito com importlib em vez de "import 08_...".
"""

from importlib import import_module
from pathlib import Path

from langgraph.store.memory import InMemoryStore

# Importar o 08 executa o módulo (carrega o modelo de embeddings e monta o agente),
# mas o chat só inicia dentro de run_chat(), protegido por __main__.
passo_08 = import_module("08_busca_semantica")
embed = passo_08.embed
EMBEDDING_DIMS = passo_08.EMBEDDING_DIMS

DOCS_DIR = Path(__file__).with_name("docs")
CHUNK_SIZE = 500  # tamanho máximo de cada chunk, em caracteres
CHUNK_OVERLAP = 100  # sobreposição entre chunks consecutivos
DOCS_NAMESPACE = ("docs",)


def load_documents(directory: Path) -> list[dict[str, str]]:
    """Lê todos os arquivos .md e .txt da pasta."""
    documents = []
    for path in sorted(directory.glob("*")):
        if path.suffix in {".md", ".txt"}:
            documents.append({"source": path.name, "text": path.read_text(encoding="utf-8")})
    return documents


def split_text(text: str, chunk_size: int, overlap: int) -> list[str]:
    """Divide o texto respeitando parágrafos; chunks longos são cortados com sobreposição."""
    chunks: list[str] = []
    current = ""
    for paragraph in (p.strip() for p in text.split("\n\n")):
        if not paragraph:
            continue
        # Cabe no chunk atual: acumula.
        if current and len(current) + len(paragraph) + 2 <= chunk_size:
            current += "\n\n" + paragraph
            continue
        if current:
            chunks.append(current)
        # Parágrafo maior que o limite: corta em janelas com sobreposição.
        while len(paragraph) > chunk_size:
            chunks.append(paragraph[:chunk_size])
            paragraph = paragraph[chunk_size - overlap:]
        current = paragraph
    if current:
        chunks.append(current)
    return chunks


def index_documents(store: InMemoryStore, documents: list[dict[str, str]]) -> int:
    """Gera os chunks de cada documento e os grava no store (com embeddings)."""
    total = 0
    for document in documents:
        chunks = split_text(document["text"], CHUNK_SIZE, CHUNK_OVERLAP)
        for number, chunk in enumerate(chunks):
            # A fonte e a posição ficam junto do texto: serão usadas para citar (passo 11).
            store.put(
                DOCS_NAMESPACE,
                f"{document['source']}#{number}",
                {"content": chunk, "source": document["source"], "chunk": number},
            )
            total += 1
    return total


if __name__ == "__main__":
    docs_store = InMemoryStore(
        index={"embed": embed, "dims": EMBEDDING_DIMS, "fields": ["content"]}
    )
    documents = load_documents(DOCS_DIR)
    print(f"{len(documents)} documentos carregados")
    print(f"{index_documents(docs_store, documents)} chunks indexados\n")

    for query in (
        "Quanto tempo leva para receber o dinheiro de volta?",
        "Posso devolver uma caneca com meu nome?",
        "A partir de quanto o frete é de graça?",
    ):
        print(f"Consulta: {query}")
        for item in docs_store.search(DOCS_NAMESPACE, query=query, limit=2):
            preview = item.value["content"].replace("\n", " ")[:90]
            print(f"  {item.score:.3f}  [{item.key}] {preview}...")
        print()
