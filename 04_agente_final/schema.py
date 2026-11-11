"""Schema do Diário de Emoções: o que é uma entrada e quais valores são permitidos.

Decisões:
- uma entrada representa um MOMENTO: um acontecimento e as emoções ligadas a ele;
- quem escolhe a emoção é a rede neural, nunca o LLM;
- as listas são fechadas para o A2 poder contar e agregar sem ambiguidade;
- o rótulo cru da RN (GoEmotions) e o grupo reduzido (Plutchik) são guardados juntos,
  então trocar o mapeamento depois não exige reclassificar nada.
"""

from typing import Literal, TypedDict, get_args

# Contexto do acontecimento. Emoção NÃO entra aqui: isso é papel da RN.
Categoria = Literal[
    "trabalho_estudos",
    "relacoes",
    "corpo_saude",  # sono, energia, alimentação, exercício
    "rotina_lazer",
    "outro",
]

# Os 27 rótulos do GoEmotions mais "neutral". É o vocabulário de saída da RN.
RotuloGoEmotions = Literal[
    "admiration", "amusement", "anger", "annoyance", "approval", "caring",
    "confusion", "curiosity", "desire", "disappointment", "disapproval",
    "disgust", "embarrassment", "excitement", "fear", "gratitude", "grief",
    "joy", "love", "nervousness", "optimism", "pride", "realization",
    "relief", "remorse", "sadness", "surprise", "neutral",
]  # fmt: skip

# Grupos reduzidos (Plutchik, 8 emoções básicas) usados na agregação do A2.
GrupoEmocao = Literal[
    "joy", "trust", "fear", "surprise", "sadness", "disgust", "anger", "anticipation", "neutral"
]

# PROPOSTA, a equipe precisa revisar. Casos discutíveis estão marcados.
GRUPO_POR_ROTULO: dict[str, GrupoEmocao] = {
    "admiration": "trust",
    "amusement": "joy",
    "anger": "anger",
    "annoyance": "anger",
    "approval": "trust",
    "caring": "trust",
    "confusion": "surprise",
    "curiosity": "anticipation",
    "desire": "anticipation",
    "disappointment": "sadness",
    "disapproval": "disgust",
    "disgust": "disgust",
    "embarrassment": "fear",  # discutível: vergonha mistura medo e aversão
    "excitement": "anticipation",
    "fear": "fear",
    "gratitude": "joy",  # discutível: alegria + confiança
    "grief": "sadness",
    "joy": "joy",
    "love": "joy",  # discutível: alegria + confiança
    "nervousness": "fear",
    "optimism": "anticipation",
    "pride": "joy",
    "realization": "surprise",
    "relief": "joy",
    "remorse": "sadness",
    "sadness": "sadness",
    "surprise": "surprise",
    "neutral": "neutral",
}

CATEGORIAS: tuple[str, ...] = get_args(Categoria)
ROTULOS: tuple[str, ...] = get_args(RotuloGoEmotions)

# Garante que o mapeamento cobre todos os rótulos e nenhum a mais.
assert set(GRUPO_POR_ROTULO) == set(ROTULOS), "mapeamento fora de sincronia com os rótulos"


class EmocaoDetectada(TypedDict):
    rotulo: RotuloGoEmotions  # saída crua da RN
    grupo: GrupoEmocao  # derivado de GRUPO_POR_ROTULO
    score: float  # confiança da RN, 0..1 (não é intensidade)
    origem: Literal["classificada", "declarada"]


class Entrada(TypedDict):
    id: str
    registrado_em: str  # ISO, preenchido pelo sistema
    ocorrido_em: str  # ISO, resolvido pelo LLM ("ontem", "semana passada")
    resumo: str  # escrito pelo LLM, é o que vira embedding
    trecho_original: str  # fala do usuário, só local, entra na RN
    categoria: Categoria
    envolve_conflito: bool
    emocoes: list[EmocaoDetectada]
