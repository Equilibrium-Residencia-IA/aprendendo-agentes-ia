"""Tools do A1: registrar_momento (escreve) e buscar_memoria (lê).

Regras de design:
- o LLM descreve o acontecimento; a emoção quem decide é a RN, dentro de registrar_momento;
- registrar_momento NÃO devolve as emoções detectadas: o A1 deve responder ao que o
  usuário disse, não anunciar o palpite do classificador como se fosse um diagnóstico;
- buscar_memoria mostra as emoções de entradas passadas, marcadas como classificação
  automática, porque ali elas são contexto histórico;
- erros de validação voltam como texto, para o LLM corrigir os argumentos e tentar de novo.
"""

from datetime import datetime
from uuid import uuid4

import chromadb
from langchain_core.tools import tool

import armazenamento
from classificador import detectar_emocoes
from schema import Categoria, Entrada

colecao: chromadb.Collection | None = None

# Resumo quase idêntico no mesmo dia é tratado como o mesmo momento. Medido: duplicatas
# 0.73-0.91, momentos distintos 0.50-0.69. Com 0.80 passam algumas paráfrases soltas
# (o prompt cobre o resto), mas não se bloqueia um momento legítimo.
DUPLICATA_SCORE = 0.80


def obter_colecao() -> chromadb.Collection:
    """Abre a coleção no primeiro uso. Os testes podem atribuir `tools.colecao` direto."""
    global colecao
    if colecao is None:
        colecao = armazenamento.abrir_colecao()
    return colecao


def _agora() -> datetime:
    return datetime.now().replace(microsecond=0)


def _normalizar_data(texto: str) -> datetime:
    """Aceita ISO com ou sem hora/fuso e devolve datetime local sem fuso."""
    try:
        data = datetime.fromisoformat(texto)
    except ValueError as erro:
        raise ValueError(
            f"Data inválida: {texto!r}. Use ISO 8601, por exemplo 2026-11-10T18:30:00."
        ) from erro
    if data.tzinfo is not None:
        data = data.astimezone().replace(tzinfo=None)
    return data


@tool
def registrar_momento(
    resumo: str,
    categoria: Categoria,
    envolve_conflito: bool,
    ocorrido_em: str,
    trecho_original: str,
) -> str:
    """Registra no diário um momento que o usuário contou (um acontecimento e como ele se sentiu).

    Use quando o usuário relatar algo que viveu, não em conversa casual.
    - resumo: 1 ou 2 frases neutras na terceira pessoa, sem nomes de terceiros.
    - categoria: o contexto do acontecimento (não a emoção).
    - envolve_conflito: true se houve discussão, tensão ou desentendimento.
    - ocorrido_em: quando aconteceu, em ISO 8601 sem fuso (ex.: 2026-11-10T18:30:00).
      Resolva "ontem", "hoje de manhã" etc. a partir da data atual informada.
    - trecho_original: as palavras do próprio usuário sobre o momento, sem alterar.
    Não inclua emoções: elas são identificadas automaticamente.
    """
    try:
        ocorrido = _normalizar_data(ocorrido_em)
        if ocorrido > _agora():
            raise ValueError(f"ocorrido_em está no futuro ({ocorrido_em}). Confira a data atual.")
        dia = ocorrido.date().isoformat()
        parecidas = armazenamento.buscar(
            obter_colecao(),
            resumo,
            top_k=1,
            desde=f"{dia}T00:00:00",
            ate=f"{dia}T23:59:59",
            min_score=DUPLICATA_SCORE,
        )
        if parecidas:
            return (
                f"Este momento já está no diário ({parecidas[0][0]['resumo']!r}). "
                "Nada foi registrado; não registre o mesmo momento de novo."
            )
        entrada: Entrada = {
            "id": str(uuid4()),
            "registrado_em": _agora().isoformat(),
            "ocorrido_em": ocorrido.isoformat(),
            "resumo": resumo.strip(),
            "trecho_original": trecho_original.strip(),
            "categoria": categoria,
            "envolve_conflito": envolve_conflito,
            "emocoes": detectar_emocoes(trecho_original),
        }
        armazenamento.gravar(obter_colecao(), entrada)
    except ValueError as erro:
        return f"Erro: {erro} Nada foi registrado; corrija os argumentos e tente de novo."
    return "Momento registrado no diário."


@tool
def buscar_memoria(
    consulta: str,
    desde: str | None = None,
    ate: str | None = None,
    categoria: Categoria | None = None,
) -> str:
    """Busca no diário momentos passados do usuário parecidos com a consulta.

    Use para lembrar de situações anteriores ("já me senti assim antes?", "como foi a semana
    passada?") ou quando o contexto do passado ajudar a responder.
    - consulta: o assunto ou situação, em linguagem natural.
    - desde / ate: limites opcionais de data em ISO 8601 (filtram pelo dia em que ocorreu).
    - categoria: filtro opcional.
    """
    try:
        achados = armazenamento.buscar(
            obter_colecao(),
            consulta,
            desde=_normalizar_data(desde).isoformat() if desde else None,
            ate=_normalizar_data(ate).isoformat() if ate else None,
            categoria=categoria,
        )
    except ValueError as erro:
        return f"Erro: {erro} Corrija os argumentos e tente de novo."
    if not achados:
        return "Nenhum momento relacionado encontrado no diário."

    linhas = []
    for entrada, score in achados:
        emocoes = ", ".join(f"{e['rotulo']} ({e['score']:.2f})" for e in entrada["emocoes"])
        conflito = ", com conflito" if entrada["envolve_conflito"] else ""
        linhas.append(
            f"- {entrada['ocorrido_em'][:10]} [{entrada['categoria']}{conflito}] {entrada['resumo']}\n"
            f"  Emoções (classificação automática, pode errar): {emocoes or 'nenhuma'}"
            f" | relevância {score:.2f}"
        )
    return "\n".join(linhas)


tools = [registrar_momento, buscar_memoria]
