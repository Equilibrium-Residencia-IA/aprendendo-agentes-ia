"""Configuração central do agente final: caminhos, modelo e parâmetros calibrados."""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

if not os.getenv("GROQ_API_KEY"):
    raise RuntimeError("A variável de ambiente GROQ_API_KEY não está configurada.")

BASE_DIR = Path(__file__).parent
DOCS_DIR = BASE_DIR / "data" / "docs"
ORDERS_FILE = BASE_DIR / "data" / "orders.json"

# Tudo que é gerado em tempo de execução fica aqui (ignorado pelo git).
STATE_DIR = BASE_DIR / "state"
STATE_DIR.mkdir(exist_ok=True)
CHROMA_DIR = STATE_DIR / "chroma"
CHECKPOINT_DB = STATE_DIR / "checkpoints.sqlite"
TICKETS_FILE = STATE_DIR / "tickets.json"

MODEL_NAME = "openai/gpt-oss-120b"
MODEL_TEMPERATURE = 0.2  # atendimento: respostas consistentes

EMBEDDING_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"

# RAG (calibrado no passo 12 de 03_langgraph).
CHUNK_SIZE = 500
CHUNK_OVERLAP = 100
DOCS_TOP_K = 3
MIN_DOC_SCORE = 0.40

# Memória de longo prazo.
MEMORY_TOP_K = 4
# Medido com o modelo de embeddings: fatos relevantes à pergunta ficam em 0.27-0.46 e
# fatos sem relação em <= 0.21.
MIN_MEMORY_SCORE = 0.25  # para injetar no prompt
# Embeddings não detectam contradição ("mora em Curitiba" x "mora em Londrina" = 0.63),
# então só duplicatas quase idênticas são descartadas automaticamente; fatos parecidos
# são mostrados ao modelo, que decide se algum ficou obsoleto (forget_memory).
MEMORY_DUPLICATE_SCORE = 0.95
MEMORY_RELATED_SCORE = 0.50

# Quantas mensagens recentes o modelo enxerga (o checkpoint guarda tudo).
MAX_HISTORY_MESSAGES = 24
