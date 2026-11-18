"""Classificador de emoções: o contrato da rede neural.

O resto do sistema só conhece detectar_emocoes(). Enquanto o modelo treinado pela equipe
não está pronto, _classificar_stub() ocupa o lugar dele. Para trocar, implemente
_classificar_modelo() e mude CLASSIFICADOR; nada mais precisa mudar.
"""

from typing import Callable

from schema import GRUPO_POR_ROTULO, EmocaoDetectada

# Contrato da RN: texto em português -> [(rótulo GoEmotions, probabilidade)].
Classificador = Callable[[str], list[tuple[str, float]]]

SCORE_MINIMO = 0.30  # abaixo disso a emoção é descartada
MAX_EMOCOES = 3  # emoções guardadas por momento


# Palavras-chave só para desenvolver o A1 sem a RN. Não é para uso real.
_PALAVRAS_STUB: dict[str, tuple[str, ...]] = {
    "nervousness": ("ansios", "nervos", "preocupa", "tenso", "tensa"),
    "sadness": ("triste", "tristeza", "chorei", "desanimad"),
    "anger": ("raiva", "furios", "irritad"),
    "annoyance": ("chate", "irrita", "incomod"),
    "joy": ("feliz", "alegr", "contente"),
    "relief": ("alivi",),
    "fear": ("medo", "assustad"),
    "disappointment": ("decepcion", "frustrad"),
    "gratitude": ("grat", "agradec"),
}


def _classificar_stub(texto: str) -> list[tuple[str, float]]:
    texto = texto.casefold()
    achados = [
        (rotulo, 0.8)
        for rotulo, palavras in _PALAVRAS_STUB.items()
        if any(palavra in texto for palavra in palavras)
    ]
    return achados or [("neutral", 0.9)]


def _classificar_modelo(texto: str) -> list[tuple[str, float]]:
    raise NotImplementedError("Conectar aqui o modelo treinado pela equipe.")


CLASSIFICADOR: Classificador = _classificar_stub


def detectar_emocoes(texto: str) -> list[EmocaoDetectada]:
    """Classifica o texto e devolve as emoções acima do limiar, da mais para a menos provável."""
    texto = texto.strip()
    if not texto:
        raise ValueError("Texto vazio: não há o que classificar.")

    previsoes = sorted(CLASSIFICADOR(texto), key=lambda par: par[1], reverse=True)
    emocoes: list[EmocaoDetectada] = []
    for rotulo, score in previsoes:
        if score < SCORE_MINIMO:
            continue
        if rotulo not in GRUPO_POR_ROTULO:
            raise ValueError(f"A RN devolveu um rótulo fora do vocabulário: {rotulo!r}")
        emocoes.append(
            {
                "rotulo": rotulo,  # type: ignore[typeddict-item]
                "grupo": GRUPO_POR_ROTULO[rotulo],
                "score": round(score, 3),
                "origem": "classificada",
            }
        )
        if len(emocoes) == MAX_EMOCOES:
            break
    return emocoes
