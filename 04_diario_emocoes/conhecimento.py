"""Base de conhecimento (RAG sobre fontes externas): PDFs científicos e educativos.

Separada do diário de propósito:
- o diário (coleção `entradas`) tem dados pessoais da pessoa; aqui só entram documentos
  públicos, e o FONTES_E_LINKS.md proíbe misturar os dois;
- as duas coleções vivem no mesmo Chroma local, mas nunca se cruzam numa busca.

Cada fonte tem `funcao` e `limitacao` (do FONTES_E_LINKS.md). A limitação viaja junto
com o trecho recuperado, para o agente não usar a fonte além do que ela permite.

Uso (a partir da raiz): python 04_diario_emocoes/conhecimento.py indexar | buscar "pergunta"
"""

import re
import sys
from pathlib import Path
from typing import TypedDict

import chromadb
from pypdf import PdfReader

import armazenamento

RECURSOS_DIR = Path(__file__).parent.parent / "RAG_resources"
COLLECTION_NAME = "conhecimento"

# O modelo de embedding trunca em 128 tokens (~500 caracteres em português): chunks
# maiores perderiam o final sem aviso.
CHUNK_SIZE = 500
CHUNK_OVERLAP = 100
MIN_SCORE = 0.30  # calibrar com `buscar` quando houver perguntas reais
TOP_K = 4


class Fonte(TypedDict):
    id: str
    titulo: str
    funcao: str
    limitacao: str


# Chave: nome do arquivo (sem a pasta). Os dois primeiros blocos seguem o
# FONTES_E_LINKS.md; os demais PDFs não constam lá, então a limitação é conservadora.
FONTES: dict[str, Fonte] = {
    "Desenvolvimento e validação de uma escala de afetos positivos e negativos.pdf": {
        "id": "ZANON_2013",
        "titulo": "Desenvolvimento e validação de uma escala de afetos positivos e negativos (Zanon et al., 2013)",
        "funcao": "Discutir afetos positivos/negativos e cuidados na interpretação de autorrelatos.",
        "limitacao": "Não importar itens/escores nem inferir validade para outros públicos ou para inferência automática via IA.",
    },
    "FAZER O QUE IMPORTA EM TEMPO DE ESTRESSE.pdf": {
        "id": "OPAS_ESTRESSE",
        "titulo": "Faça o que importa em tempos de estresse (OPAS/OMS, versão Brasil)",
        "funcao": "Consulta educativa sobre estresse, pensamentos, emoções e estratégias de enfrentamento.",
        "limitacao": "Não usar como escala, teste diagnóstico ou cálculo de intensidade emocional.",
    },
    "2005_Scherer_SSI.pdf": {
        "id": "SCHERER_2005",
        "titulo": "What are emotions? And how can they be measured? (Scherer, 2005)",
        "funcao": "Conceitos sobre o que são emoções e como se medem (em inglês).",
        "limitacao": "Fonte teórica fora do catálogo oficial; não usar para classificar ou diagnosticar a pessoa.",
    },
    "Normas de Alerta e Valência para 908 Palavras da Língua Portuguesa.pdf": {
        "id": "OLIVEIRA_2013_NORMAS",
        "titulo": "Normas de alerta e valência para 908 palavras da língua portuguesa (Oliveira, 2013)",
        "funcao": "Contexto sobre valência (agradável/desagradável) e alerta de palavras em português.",
        "limitacao": "Fonte fora do catálogo oficial; normas de palavras não servem para inferir o estado emocional de alguém.",
    },
    "Evidências de Validade de Marcadores Reduzidos para a Avaliação da  Personalidade no Modelo dos Cinco Grandes Fatores.pdf": {
        "id": "BIG5_MARCADORES_2012",
        "titulo": "Marcadores reduzidos para avaliação da personalidade nos Cinco Grandes Fatores (2012)",
        "funcao": "Contexto sobre personalidade no modelo dos Cinco Grandes Fatores.",
        "limitacao": "Fonte fora do catálogo oficial; não rotular a personalidade da pessoa.",
    },
    # Atenção: apesar do nome terminar em "1", este PDF é outro artigo (o ERQ).
    "Evidências de Validade de Marcadores Reduzidos para a Avaliação da  Personalidade no Modelo dos Cinco Grandes Fatores1.pdf": {
        "id": "ERQ_IDOSOS",
        "titulo": "Emotional Regulation Questionnaire (ERQ): indicadores psicométricos em amostra idosa",
        "funcao": "Contexto sobre regulação emocional (reavaliação cognitiva e supressão).",
        "limitacao": "Fonte fora do catálogo oficial; não aplicar o questionário nem pontuar a pessoa.",
    },
}

_RE_REFERENCIAS = re.compile(r"^\s*(refer[eê]ncias( bibliogr[aá]ficas)?|references)\s*$", re.I | re.M)
_RE_ESPACOS = re.compile(r"[ \t]+")


def ler_pdf(caminho: Path) -> str:
    """Texto do PDF, sem a lista de referências (ruído para a busca)."""
    paginas = [(p.extract_text() or "") for p in PdfReader(caminho).pages]
    texto = "\n".join(paginas)
    texto = re.sub(r"-\n(?=[a-zà-ú])", "", texto)  # junta palavras hifenizadas na quebra de linha
    cortes = [m.start() for m in _RE_REFERENCIAS.finditer(texto)]
    if cortes and cortes[-1] > len(texto) * 0.6:
        texto = texto[: cortes[-1]]
    return texto


def _paragrafos(texto: str) -> list[str]:
    """Quebra por linha em branco; sem elas (comum em PDF), junta as linhas e quebra em frases."""
    blocos = [b for b in (re.sub(r"\s*\n\s*", " ", p).strip() for p in texto.split("\n\n")) if b]
    if len(blocos) > 5:
        return blocos
    corrido = re.sub(r"\s*\n\s*", " ", texto)
    return [s for s in re.split(r"(?<=[.!?])\s+(?=[A-ZÀ-Ú])", _RE_ESPACOS.sub(" ", corrido)) if s.strip()]


def dividir(texto: str, tamanho: int = CHUNK_SIZE, sobreposicao: int = CHUNK_OVERLAP) -> list[str]:
    """Agrupa parágrafos/frases até `tamanho`; peças maiores são cortadas com sobreposição."""
    chunks: list[str] = []
    atual = ""
    for peca in _paragrafos(texto):
        if atual and len(atual) + len(peca) + 1 <= tamanho:
            atual += " " + peca
            continue
        if atual:
            chunks.append(atual)
        while len(peca) > tamanho:
            corte = peca.rfind(" ", 0, tamanho) if " " in peca[:tamanho] else tamanho  # não parte palavra
            chunks.append(peca[:corte])
            inicio = max(corte - sobreposicao, 1)
            peca = peca[peca.find(" ", inicio) + 1 :] if " " in peca[inicio:corte] else peca[corte:]
        atual = peca
    if atual:
        chunks.append(atual)
    return chunks


def _util(chunk: str) -> bool:
    """Descarta tabelas de números, cabeçalhos e trechos sem prosa (poucas letras)."""
    letras = sum(c.isalpha() for c in chunk)
    return len(chunk) >= 80 and letras / len(chunk) >= 0.65


def abrir_colecao(caminho: Path | None = None) -> chromadb.Collection:
    return armazenamento.abrir_colecao(caminho, nome=COLLECTION_NAME)


def indexar(colecao: chromadb.Collection, pasta: Path = RECURSOS_DIR) -> dict[str, int]:
    """Reconstrói a coleção do zero (idempotente). Devolve {id da fonte: nº de chunks}."""
    existentes = colecao.get()["ids"]
    if existentes:
        colecao.delete(ids=existentes)

    contagem: dict[str, int] = {}
    for caminho in sorted(pasta.rglob("*.pdf")):
        fonte = FONTES.get(caminho.name)
        if fonte is None:
            print(f"[aviso] PDF sem entrada em FONTES, ignorado: {caminho.name}")
            continue
        chunks = [c for c in dividir(ler_pdf(caminho)) if _util(c)]
        if not chunks:
            print(f"[aviso] nenhum texto aproveitável em {caminho.name}")
            continue
        colecao.add(
            ids=[f"{fonte['id']}#{n}" for n in range(len(chunks))],
            documents=chunks,
            embeddings=armazenamento.embed(chunks),
            metadatas=[
                {
                    "fonte_id": fonte["id"],
                    "titulo": fonte["titulo"],
                    "funcao": fonte["funcao"],
                    "limitacao": fonte["limitacao"],
                    "chunk": n,
                }
                for n in range(len(chunks))
            ],
        )
        contagem[fonte["id"]] = len(chunks)
    return contagem


def buscar(
    colecao: chromadb.Collection, consulta: str, top_k: int = TOP_K, min_score: float = MIN_SCORE
) -> list[tuple[str, dict, float]]:
    """Retorna (trecho, metadados, score), do mais ao menos parecido, acima de min_score."""
    if colecao.count() == 0:
        return []
    r = colecao.query(
        query_embeddings=armazenamento.embed([consulta]),
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )
    achados = zip(r["documents"][0], r["metadatas"][0], (1 - d for d in r["distances"][0]))
    return [(doc, meta, score) for doc, meta, score in achados if score >= min_score]


if __name__ == "__main__":
    comando = sys.argv[1] if len(sys.argv) > 1 else ""
    if comando == "indexar":
        for id_, n in indexar(abrir_colecao()).items():
            print(f"{id_}: {n} trechos")
    elif comando == "buscar" and len(sys.argv) > 2:
        for doc, meta, score in buscar(abrir_colecao(), " ".join(sys.argv[2:]), min_score=0.0):
            print(f"[{score:.2f}] {meta['fonte_id']}#{meta['chunk']}: {doc[:200]}\n")
    else:
        print('Uso: conhecimento.py indexar | buscar "pergunta"')
