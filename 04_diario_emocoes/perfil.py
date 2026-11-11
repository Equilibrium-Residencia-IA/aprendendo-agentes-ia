"""Perfil vivo: resumo curto do usuário, reescrito a partir das entradas novas do diário.

- fica em state/perfil.md (on-device) e é lido pelo A1 a cada chamada;
- state/perfil_meta.json guarda até qual `registrado_em` o perfil já incorporou;
- só atualiza com MIN_NOVAS entradas novas, para não gastar LLM a cada conversa;
- o perfil descreve tendências observadas, nunca condições: se a saída do LLM sair vazia,
  longa demais ou com linguagem de diagnóstico, o perfil anterior é mantido.
"""

import json
import os
import re
from collections.abc import Callable
from pathlib import Path

import chromadb

import armazenamento
from armazenamento import STATE_DIR
from schema import Entrada

MIN_NOVAS = 3
MAX_CARACTERES = 1200
MAX_ENTRADAS_POR_ATUALIZACAO = 40  # limita o tamanho do prompt

DIAGNOSTICO = re.compile(
    r"diagn[oó]stic|\b(tem|sofre de|apresenta|possui|portador)\b\s+(uma?\s+)?"
    r"(depress|ansiedade|transtorn|burnout|tdah|bipolar)",
    re.IGNORECASE,
)

PROMPT_PERFIL = """Você mantém o perfil de uma pessoa que usa um diário de emoções. O perfil ajuda \
um assistente acolhedor a conhecê-la melhor. Reescreva o perfil completo, integrando o perfil \
atual com as entradas novas.

Regras:
- Descreva apenas o que as entradas sustentam. Só use "costuma" ou "tende a" quando houver \
pelo menos duas entradas sobre o mesmo contexto; fato que apareceu uma única vez deve dizer \
"uma vez" ou "em uma ocasião".
- Agrupe tópicos parecidos em um único item e dê prioridade ao que se repete; fatos isolados \
antigos podem ser resumidos ou omitidos para o perfil continuar curto.
- NUNCA diagnostique nem nomeie condições ou transtornos. Escreva "costuma ficar ansioso em \
apresentações", e não "tem ansiedade".
- As emoções vêm de um classificador automático e podem errar: use-as como indício, não como fato.
- Não inclua nomes de outras pessoas nem dados que identifiquem alguém.
- Mantenha o que o perfil atual já tinha, a menos que as entradas novas o contradigam.
- Texto curto, em português, em tópicos, no máximo 150 palavras. Devolva só o perfil."""


def _caminhos(pasta: Path) -> tuple[Path, Path]:
    return pasta / "perfil.md", pasta / "perfil_meta.json"


def carregar_perfil(pasta: Path = STATE_DIR) -> str:
    caminho, _ = _caminhos(pasta)
    try:
        return caminho.read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        return ""


def _cursor(pasta: Path) -> str:
    _, meta = _caminhos(pasta)
    try:
        return json.loads(meta.read_text(encoding="utf-8"))["ate_registrado_em"]
    except (FileNotFoundError, KeyError, json.JSONDecodeError):
        return ""


def _escrever(caminho: Path, conteudo: str) -> None:
    """Escrita atômica: um crash no meio nunca deixa o arquivo pela metade."""
    caminho.parent.mkdir(parents=True, exist_ok=True)
    temporario = caminho.with_suffix(caminho.suffix + ".tmp")
    temporario.write_text(conteudo, encoding="utf-8")
    os.replace(temporario, caminho)


def entradas_novas(colecao: chromadb.Collection, pasta: Path = STATE_DIR) -> list[Entrada]:
    cursor = _cursor(pasta)
    return [e for e in armazenamento.listar(colecao) if e["registrado_em"] > cursor]


def _formatar_entradas(entradas: list[Entrada]) -> str:
    linhas = []
    for e in entradas:
        # "neutral" significa que a RN não achou emoção; não é um traço da pessoa.
        emocoes = ", ".join(x["rotulo"] for x in e["emocoes"] if x["rotulo"] != "neutral")
        emocoes = emocoes or "nenhuma identificada"
        conflito = ", com conflito" if e["envolve_conflito"] else ""
        linhas.append(
            f"- {e['ocorrido_em'][:10]} [{e['categoria']}{conflito}] {e['resumo']} "
            f"(emoções automáticas: {emocoes})"
        )
    return "\n".join(linhas)


def _gerar_com_llm(prompt: str) -> str:
    from langchain_groq import ChatGroq  # importado aqui: só atualizar precisa do LLM

    modelo = ChatGroq(model="openai/gpt-oss-120b", temperature=0.2, max_retries=6)
    return str(modelo.invoke(prompt).content)


def _valido(texto: str) -> str | None:
    """Devolve o motivo da rejeição, ou None se o perfil serve."""
    if not texto.strip():
        return "vazio"
    if len(texto) > MAX_CARACTERES:
        return f"longo demais ({len(texto)} caracteres)"
    if DIAGNOSTICO.search(texto):
        return "linguagem de diagnóstico"
    return None


def atualizar_perfil(
    colecao: chromadb.Collection,
    pasta: Path = STATE_DIR,
    gerar: Callable[[str], str] = _gerar_com_llm,
    minimo: int = MIN_NOVAS,
) -> str:
    """Atualiza o perfil se houver entradas novas suficientes. Devolve uma linha de status."""
    novas = entradas_novas(colecao, pasta)
    if len(novas) < minimo:
        return f"Perfil mantido ({len(novas)} entradas novas, mínimo {minimo})."

    lote = sorted(novas, key=lambda e: e["registrado_em"])[:MAX_ENTRADAS_POR_ATUALIZACAO]
    atual = carregar_perfil(pasta) or "(ainda não há perfil)"
    base = f"{PROMPT_PERFIL}\n\nPerfil atual:\n{atual}\n\nEntradas novas:\n{_formatar_entradas(lote)}"

    motivo = ""
    for tentativa in range(2):
        aviso = f"\n\nA versão anterior foi rejeitada ({motivo}). Corrija." if tentativa else ""
        texto = gerar(base + aviso).strip()
        motivo = _valido(texto) or ""
        if not motivo:
            break
    else:
        return f"Perfil mantido: a saída do LLM foi rejeitada ({motivo})."

    perfil_path, meta_path = _caminhos(pasta)
    _escrever(perfil_path, texto + "\n")
    # O marcador avança só até a última entrada do lote, para o resto entrar na próxima vez.
    _escrever(meta_path, json.dumps({"ate_registrado_em": lote[-1]["registrado_em"]}))
    return f"Perfil atualizado com {len(lote)} entradas novas."
