"""Avaliação da recuperação: mede hit@1, hit@3, MRR e a rejeição de perguntas fora do escopo.

Cada pergunta cobre uma informação identificada por uma frase-chave que deve aparecer
no chunk recuperado (assim a avaliação não depende do tamanho do chunk).
Varre vários CHUNK_SIZE e limiares para escolher os melhores valores.
Não usa o LLM: só embeddings e busca, então roda rápido e sem custo.
"""

from importlib import import_module

import chromadb

passo_09 = import_module("09_documentos")
passo_12 = import_module("12_rag_persistente")

# (pergunta, frase-chave que o chunk correto deve conter)
IN_SCOPE = [
    ("Quanto tempo tenho para devolver um produto?", "7 dias corridos"),
    ("Qual o prazo se o produto veio com defeito?", "90 dias"),
    ("Posso devolver uma caneca com nome gravado?", "Produtos personalizados"),
    ("Em que condição o produto deve estar para devolver?", "embalagem original"),
    ("Como peço a devolução?", "suporte@aurora.example"),
    ("A etiqueta de postagem reversa é cobrada?", "etiqueta de postagem reversa gratuita"),
    ("Quanto tempo leva o reembolso no cartão de crédito?", "estornados na fatura"),
    ("E se eu paguei com Pix, em quanto tempo recebo?", "em até 24 horas"),
    ("Quais as modalidades de frete?", "Econômica"),
    ("Qual o prazo do frete expresso?", "1 a 3 dias úteis"),
    ("Qual o valor mínimo para frete grátis no Sul?", "R$ 250,00"),
    ("Quando recebo o código de rastreio?", "código de rastreio"),
    ("O que acontece se eu não estiver em casa na entrega?", "três vezes"),
    ("Posso cancelar se a entrega falhar?", "cancelamento com reembolso"),
]
OUT_OF_SCOPE = [
    "Vocês aceitam boleto?",
    "Qual o telefone da loja?",
    "Vocês têm loja física?",
    "Qual a capital da França?",
    "Como faço para trocar a senha da conta?",
    "Vocês vendem produtos usados?",
]

CHUNK_SIZES = [200, 350, 500, 800]
THRESHOLDS = [0.30, 0.35, 0.40, 0.45, 0.50]
TOP_K = 3


def build_collection(client: chromadb.ClientAPI, chunk_size: int) -> chromadb.Collection:
    try:
        client.delete_collection(passo_12.COLLECTION_NAME)
    except Exception:
        pass
    collection = passo_12.get_collection(client)
    overlap = min(passo_09.CHUNK_OVERLAP, chunk_size // 4)
    passo_12.sync_index(collection, passo_09.load_documents(passo_09.DOCS_DIR), chunk_size, overlap)
    return collection


def evaluate(collection: chromadb.Collection) -> dict:
    ranks = []
    for question, key_phrase in IN_SCOPE:
        hits = passo_12.search(collection, question, TOP_K)
        rank = next((i + 1 for i, (_, _, text) in enumerate(hits) if key_phrase in text), None)
        ranks.append(rank)
    top_in_scope = [passo_12.search(collection, q, 1)[0][1] for q, _ in IN_SCOPE]
    top_out_scope = [passo_12.search(collection, q, 1)[0][1] for q in OUT_OF_SCOPE]
    return {
        "hit1": sum(r == 1 for r in ranks) / len(ranks),
        "hit3": sum(r is not None for r in ranks) / len(ranks),
        "mrr": sum(1 / r for r in ranks if r) / len(ranks),
        "in_scores": top_in_scope,
        "out_scores": top_out_scope,
    }


if __name__ == "__main__":
    client = chromadb.EphemeralClient()
    print(f"{len(IN_SCOPE)} perguntas no escopo, {len(OUT_OF_SCOPE)} fora do escopo\n")
    print("chunk | chunks | hit@1 | hit@3 |  MRR")
    results = {}
    for size in CHUNK_SIZES:
        collection = build_collection(client, size)
        results[size] = evaluate(collection)
        r = results[size]
        print(f"{size:5d} | {collection.count():6d} | {r['hit1']:.2f}  | {r['hit3']:.2f}  | {r['mrr']:.2f}")

    print("\nLimiar: (no escopo que passam o limiar / fora do escopo rejeitadas)")
    print("chunk | " + " | ".join(f"{t:.2f}" for t in THRESHOLDS))
    for size in CHUNK_SIZES:
        r = results[size]
        cells = []
        for t in THRESHOLDS:
            answered = sum(s >= t for s in r["in_scores"]) / len(r["in_scores"])
            rejected = sum(s < t for s in r["out_scores"]) / len(r["out_scores"])
            cells.append(f"{answered:.2f}/{rejected:.2f}")
        print(f"{size:5d} | " + " | ".join(cells))
