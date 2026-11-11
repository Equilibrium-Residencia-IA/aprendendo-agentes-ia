"""Sétimo passo: embeddings e similaridade semântica (a base do RAG).

Sem LLM e sem grafo: só transformamos textos em vetores e comparamos.
"""

import numpy as np
from sentence_transformers import SentenceTransformer

# Modelo multilíngue local (roda na CPU, sem API key). Baixa ~470MB na primeira vez.
model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")

# Memórias de exemplo, como as do memoria.json.
documents = [
    "Prefere respostas curtas",
    "Gosta de Python",
    "O nome do usuário é João Pedro",
    "Mora em Campinas",
    "Tem um cachorro chamado Thor",
]

# Consultas que quase não compartilham palavras com as memórias.
queries = [
    "Como devo me dirigir a ele?",
    "Qual linguagem de programação ele curte?",
    "Qual o nome do pet?",
    "Em que cidade ele vive?",
]

# encode devolve um vetor por texto. normalize_embeddings=True deixa cada vetor
# com tamanho 1, então o produto escalar equivale à similaridade de cosseno.
doc_vectors = model.encode(documents, normalize_embeddings=True)
query_vectors = model.encode(queries, normalize_embeddings=True)

print(f"Dimensão de cada vetor: {doc_vectors.shape[1]}\n")

# Matriz [consultas x documentos] com todas as similaridades de uma vez.
scores = query_vectors @ doc_vectors.T

for query, row in zip(queries, scores):
    print(f"Consulta: {query}")
    for index in np.argsort(row)[::-1][:3]:
        print(f"  {row[index]:.3f}  {documents[index]}")
    print()
