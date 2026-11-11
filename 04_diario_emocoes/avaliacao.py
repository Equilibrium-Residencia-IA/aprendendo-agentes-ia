"""Avaliação do diário. Rode a partir da raiz:

    python 04_diario_emocoes/avaliacao.py recuperacao

recuperacao: mede hit@1, hit@3, MRR e a rejeição de consultas sem relação, varrendo
os limiares de similaridade. Não usa o LLM, só embeddings e busca.
"""

import sys
import tempfile
from pathlib import Path

import armazenamento
from classificador import detectar_emocoes
from schema import Entrada

# Momentos como o LLM os resumiria: terceira pessoa, neutros.
# (id, resumo, categoria, envolve_conflito, ocorrido_em)
ENTRADAS = [
    ("a1", "Discutiu com o chefe sobre um prazo e ficou ansioso o resto do dia", "trabalho_estudos", True, "2026-11-03T15:00:00"),
    ("a2", "Dormiu cerca de quatro horas e passou o dia sem energia", "corpo_saude", False, "2026-11-04T08:00:00"),
    ("a3", "Jantou com amigos de longa data e se sentiu feliz e acolhido", "relacoes", False, "2026-11-05T21:00:00"),
    ("a4", "Brigou com o irmão por causa da divisão de tarefas em casa", "relacoes", True, "2026-11-06T19:00:00"),
    ("a5", "Passou na prova final da faculdade e sentiu muito alívio", "trabalho_estudos", False, "2026-11-07T11:00:00"),
    ("a6", "Ficou sozinho no fim de semana e sentiu tristeza e solidão", "rotina_lazer", False, "2026-11-08T16:00:00"),
    ("a7", "Apresentou um trabalho para a turma e ficou nervoso antes de começar", "trabalho_estudos", False, "2026-11-09T10:00:00"),
    ("a8", "Fez uma caminhada no parque e se sentiu mais calmo", "rotina_lazer", False, "2026-11-09T18:00:00"),
    ("a9", "Recebeu uma crítica injusta de um colega e ficou irritado", "trabalho_estudos", True, "2026-11-10T14:00:00"),
    ("a10", "Acordou com dor de cabeça e ficou desanimado", "corpo_saude", False, "2026-11-10T07:00:00"),
]  # fmt: skip

# (consulta, ids que deveriam aparecer)
NO_ESCOPO = [
    ("já fiquei ansioso no trabalho?", {"a1", "a7"}),
    ("como tenho dormido?", {"a2"}),
    ("quando me senti sozinho?", {"a6"}),
    ("brigas com a família", {"a4"}),
    ("fiquei nervoso antes de apresentar algo", {"a7"}),
    ("situações em que me senti feliz com outras pessoas", {"a3"}),
    ("o que me ajuda a ficar calmo?", {"a8"}),
    ("conflitos com colegas de trabalho", {"a9", "a1"}),
    ("momentos de alívio", {"a5"}),
    ("tive mal-estar físico", {"a10"}),
]
FORA_DO_ESCOPO = [
    "qual a capital da França?",
    "receita de bolo de cenoura",
    "como instalar o Python?",
    "previsão do tempo para amanhã",
    "resultado do jogo de ontem",
]

LIMIARES = [0.15, 0.20, 0.25, 0.30, 0.35, 0.40]
TOP_K = 5


def montar_entrada(id_: str, resumo: str, categoria: str, conflito: bool, quando: str) -> Entrada:
    return {
        "id": id_,
        "registrado_em": quando,
        "ocorrido_em": quando,
        "resumo": resumo,
        "trecho_original": resumo,
        "categoria": categoria,  # type: ignore[typeddict-item]
        "envolve_conflito": conflito,
        "emocoes": detectar_emocoes(resumo),
    }


def semear(colecao) -> None:
    for dados in ENTRADAS:
        armazenamento.gravar(colecao, montar_entrada(*dados))


def avaliar_recuperacao() -> None:
    with tempfile.TemporaryDirectory() as pasta:
        colecao = armazenamento.abrir_colecao(Path(pasta))
        semear(colecao)

        # min_score=0 devolve o ranking cru; o limiar é aplicado depois, na varredura.
        ranking = {
            consulta: [
                (e["id"], s)
                for e, s in armazenamento.buscar(colecao, consulta, top_k=TOP_K, min_score=-1)
            ]
            for consulta, _ in NO_ESCOPO
        }
        ruido = {
            consulta: armazenamento.buscar(colecao, consulta, top_k=1, min_score=-1)[0][1]
            for consulta in FORA_DO_ESCOPO
        }

    posicoes = []
    for consulta, esperados in NO_ESCOPO:
        ids = [id_ for id_, _ in ranking[consulta]]
        posicoes.append(next((i + 1 for i, id_ in enumerate(ids) if id_ in esperados), None))
    n = len(posicoes)
    print(f"{len(ENTRADAS)} entradas, {n} consultas no escopo, {len(FORA_DO_ESCOPO)} fora\n")
    print(f"hit@1 {sum(p == 1 for p in posicoes) / n:.2f} | "
          f"hit@3 {sum(p is not None and p <= 3 for p in posicoes) / n:.2f} | "
          f"MRR {sum(1 / p for p in posicoes if p) / n:.2f}")
    for (consulta, _), pos in zip(NO_ESCOPO, posicoes):
        if pos != 1:
            print(f"  não ficou em 1º ({pos}): {consulta}")

    melhor_no_escopo = [ranking[c][0][1] for c, _ in NO_ESCOPO]
    print(f"\nmelhor score, no escopo: min {min(melhor_no_escopo):.2f} / média "
          f"{sum(melhor_no_escopo) / n:.2f}")
    print(f"melhor score, fora do escopo: máx {max(ruido.values()):.2f}")
    for consulta, score in sorted(ruido.items(), key=lambda par: -par[1]):
        print(f"  {score:.2f}  {consulta}")

    print("\nlimiar | recall | precisão | fora rejeitado")
    for limiar in LIMIARES:
        achados = relevantes = devolvidos = 0
        for consulta, esperados in NO_ESCOPO:
            acima = [id_ for id_, s in ranking[consulta] if s >= limiar]
            devolvidos += len(acima)
            relevantes += len(esperados)
            achados += len(esperados & set(acima))
        rejeitados = sum(score < limiar for score in ruido.values())
        precisao = achados / devolvidos if devolvidos else float("nan")
        print(f"  {limiar:.2f} |  {achados / relevantes:.2f}  |   {precisao:.2f}   |"
              f"   {rejeitados}/{len(FORA_DO_ESCOPO)}")


if __name__ == "__main__":
    modo = sys.argv[1] if len(sys.argv) > 1 else "recuperacao"
    if modo == "recuperacao":
        avaliar_recuperacao()
    else:
        sys.exit(f"Modo desconhecido: {modo!r}. Use: recuperacao")
