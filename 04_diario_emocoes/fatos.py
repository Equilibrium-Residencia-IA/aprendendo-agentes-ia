"""Fatos estáveis sobre o usuário (nome, idade, pessoas próximas), em state/fatos.json.

Diferente do diário (momentos com emoção) e do perfil (resumo de tendências), aqui ficam
dados simples que o usuário diz uma vez e espera que sejam lembrados. O A1 grava com a
tool lembrar_fato e o prompt injeta tudo a cada chamada. A mesma chave sobrescreve o valor.
"""

import json
from pathlib import Path

from armazenamento import STATE_DIR

MAX_FATOS = 30
MAX_TEXTO = 120


def _caminho(pasta: Path) -> Path:
    return pasta / "fatos.json"


def carregar_fatos(pasta: Path = STATE_DIR) -> dict[str, str]:
    try:
        dados = json.loads(_caminho(pasta).read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}
    return {str(k): str(v) for k, v in dados.items()} if isinstance(dados, dict) else {}


def salvar_fato(chave: str, valor: str, pasta: Path = STATE_DIR) -> None:
    chave, valor = chave.strip().lower(), valor.strip()
    if not chave or not valor:
        raise ValueError("chave e valor não podem ser vazios.")
    if len(chave) > MAX_TEXTO or len(valor) > MAX_TEXTO:
        raise ValueError(f"chave e valor devem ter até {MAX_TEXTO} caracteres.")
    fatos = carregar_fatos(pasta)
    if chave not in fatos and len(fatos) >= MAX_FATOS:
        raise ValueError(f"limite de {MAX_FATOS} fatos atingido.")
    fatos[chave] = valor
    pasta.mkdir(parents=True, exist_ok=True)
    caminho = _caminho(pasta)
    temporario = caminho.with_suffix(".tmp")
    temporario.write_text(json.dumps(fatos, ensure_ascii=False, indent=2), encoding="utf-8")
    temporario.replace(caminho)


def formatar_fatos(pasta: Path = STATE_DIR) -> str:
    return "\n".join(f"- {k}: {v}" for k, v in carregar_fatos(pasta).items())
