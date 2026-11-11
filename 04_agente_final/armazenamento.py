"""Armazenamento das entradas do diário em um Chroma local (on-device).

- o documento indexado é o `resumo`; o embedding é gerado localmente;
- o Chroma só aceita metadados simples (str, int, float, bool), então as emoções vão
  serializadas em JSON, e o grupo dominante fica num campo à parte para filtrar;
- datas ficam em ISO (legível) e também em timestamp numérico, porque o Chroma só
  compara intervalos com números.
"""

import json
from datetime import datetime
from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer

from schema import CATEGORIAS, Categoria, EmocaoDetectada, Entrada

STATE_DIR = Path(__file__).with_name("state")
COLLECTION_NAME = "entradas"
MODELO_EMBEDDING = "paraphrase-multilingual-MiniLM-L12-v2"  # o mesmo do 03_langgraph
MIN_SCORE = 0.25  # similaridade mínima; valor inicial, calibrar com exemplos reais

_modelo: SentenceTransformer | None = None


def embed(textos: list[str]) -> list[list[float]]:
    """Carrega o modelo só no primeiro uso (o carregamento é lento)."""
    global _modelo
    if _modelo is None:
        _modelo = SentenceTransformer(MODELO_EMBEDDING)
    return _modelo.encode(textos, normalize_embeddings=True).tolist()


def abrir_colecao(caminho: Path | None = None) -> chromadb.Collection:
    """Abre (ou cria) a coleção. `caminho` existe para os testes usarem uma pasta temporária."""
    cliente = chromadb.PersistentClient(path=str(caminho or STATE_DIR / "chroma"))
    return cliente.get_or_create_collection(COLLECTION_NAME, metadata={"hnsw:space": "cosine"})


def _timestamp(iso: str) -> float:
    return datetime.fromisoformat(iso).timestamp()


def _grupo_dominante(emocoes: list[EmocaoDetectada]) -> str:
    """Grupo da emoção de maior score; 'nenhuma' se a RN não passou o limiar em nada."""
    return max(emocoes, key=lambda e: e["score"])["grupo"] if emocoes else "nenhuma"


def gravar(colecao: chromadb.Collection, entrada: Entrada) -> None:
    """Valida e grava uma entrada. Levanta ValueError com mensagem clara se algo estiver errado."""
    if not entrada["resumo"].strip():
        raise ValueError("O resumo não pode estar vazio.")
    if entrada["categoria"] not in CATEGORIAS:
        raise ValueError(f"Categoria inválida: {entrada['categoria']!r}. Use uma de {CATEGORIAS}.")
    try:
        ocorrido_ts = _timestamp(entrada["ocorrido_em"])
    except ValueError as erro:
        raise ValueError(f"ocorrido_em não é uma data ISO válida: {entrada['ocorrido_em']!r}") from erro

    colecao.add(
        ids=[entrada["id"]],
        documents=[entrada["resumo"]],
        embeddings=embed([entrada["resumo"]]),
        metadatas=[
            {
                "registrado_em": entrada["registrado_em"],
                "ocorrido_em": entrada["ocorrido_em"],
                "ocorrido_ts": ocorrido_ts,
                "categoria": entrada["categoria"],
                "envolve_conflito": entrada["envolve_conflito"],
                "grupo_dominante": _grupo_dominante(entrada["emocoes"]),
                "emocoes_json": json.dumps(entrada["emocoes"], ensure_ascii=False),
                "trecho_original": entrada["trecho_original"],
            }
        ],
    )


def _montar_entrada(id_: str, resumo: str, meta: dict) -> Entrada:
    return {
        "id": id_,
        "registrado_em": meta["registrado_em"],
        "ocorrido_em": meta["ocorrido_em"],
        "resumo": resumo,
        "trecho_original": meta["trecho_original"],
        "categoria": meta["categoria"],
        "envolve_conflito": meta["envolve_conflito"],
        "emocoes": json.loads(meta["emocoes_json"]),
    }


def _filtro(desde: str | None, ate: str | None, categoria: Categoria | None) -> dict | None:
    condicoes: list[dict] = []
    if desde:
        condicoes.append({"ocorrido_ts": {"$gte": _timestamp(desde)}})
    if ate:
        condicoes.append({"ocorrido_ts": {"$lte": _timestamp(ate)}})
    if categoria:
        condicoes.append({"categoria": categoria})
    if not condicoes:
        return None
    return condicoes[0] if len(condicoes) == 1 else {"$and": condicoes}


def buscar(
    colecao: chromadb.Collection,
    consulta: str,
    top_k: int = 5,
    desde: str | None = None,
    ate: str | None = None,
    categoria: Categoria | None = None,
    min_score: float = MIN_SCORE,
) -> list[tuple[Entrada, float]]:
    """Busca por similaridade com o resumo. Retorna (entrada, score), do mais ao menos parecido.

    O Chroma devolve distância de cosseno; score = 1 - distância. Resultados abaixo de
    min_score são descartados.
    """
    if colecao.count() == 0:
        return []
    resultado = colecao.query(
        query_embeddings=embed([consulta]),
        n_results=top_k,
        where=_filtro(desde, ate, categoria),
        include=["documents", "metadatas", "distances"],
    )
    achados = [
        (_montar_entrada(id_, resumo, meta), 1 - distancia)
        for id_, resumo, meta, distancia in zip(
            resultado["ids"][0],
            resultado["documents"][0],
            resultado["metadatas"][0],
            resultado["distances"][0],
        )
    ]
    return [(entrada, score) for entrada, score in achados if score >= min_score]
