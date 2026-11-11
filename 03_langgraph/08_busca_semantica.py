"""Oitavo passo: busca semântica de memórias com embeddings no store do LangGraph.

Diferenças em relação ao 06:
- o InMemoryStore indexa o campo "content" com embeddings;
- retrieve_memory usa store.search(query=...), que ordena por similaridade;
- um limiar mínimo (MIN_SCORE) descarta resultados pouco relacionados;
- o fallback por palavras-chave (memory_intent) foi removido.
"""

import os
from datetime import datetime
from typing import Annotated, Literal
from uuid import uuid4

from dotenv import load_dotenv
from langchain_core.messages import AIMessage, AnyMessage, HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from langchain_groq import ChatGroq
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import START, MessagesState, StateGraph
from langgraph.prebuilt import InjectedState, InjectedStore, ToolNode
from langgraph.store.base import BaseStore
from langgraph.store.memory import InMemoryStore
from sentence_transformers import SentenceTransformer


load_dotenv()

if not os.getenv("GROQ_API_KEY"):
    raise RuntimeError("A variável de ambiente GROQ_API_KEY não está configurada.")


MAX_RETRIEVED_MEMORIES = 5
# Similaridade mínima para uma memória ser considerada relevante.
# Valor inicial; o ideal é calibrá-lo com exemplos reais (passo 12).
MIN_SCORE = 0.25

SYSTEM_PROMPT = """Você é um assistente com memória de longo prazo.
Quando o usuário pedir para lembrar, salvar ou guardar uma preferência ou fato,
use obrigatoriamente a ferramenta save_memory antes de responder.
Quando o usuário perguntar algo que dependa de informações pessoais dele
(nome, preferências, fatos que ele já contou), use a ferramenta retrieve_memory
antes de responder.
Não diga que salvou ou encontrou uma memória sem executar a ferramenta.
Responda em português e seja claro."""


# Modelo de embeddings local, o mesmo do passo 07.
embedding_model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
EMBEDDING_DIMS = embedding_model.get_embedding_dimension()


def embed(texts: list[str]) -> list[list[float]]:
    """Função de embedding que o store chama ao salvar e ao buscar."""
    return embedding_model.encode(texts, normalize_embeddings=True).tolist()


class AgentState(MessagesState):
    """Estado da conversa, incluindo o identificador do usuário."""

    user_id: str


def memory_namespace(user_id: str) -> tuple[str, str]:
    """Define o namespace que separa as memórias de cada usuário."""
    return (user_id, "memories")


@tool
def save_memory(
    content: str,
    user_id: Annotated[str, InjectedState("user_id")],
    store: Annotated[BaseStore, InjectedStore],
) -> str:
    """Salva uma preferência ou fato importante para conversas futuras."""
    normalized_content = content.strip()
    if not normalized_content:
        raise ValueError("A memória não pode estar vazia.")

    namespace = memory_namespace(user_id)
    # Sem query, search apenas lista os itens do namespace.
    existing = store.search(namespace, limit=100)
    if any(
        item.value.get("content", "").casefold() == normalized_content.casefold()
        for item in existing
    ):
        return "Essa memória já está salva."

    # O store gera o embedding de "content" automaticamente no put.
    store.put(
        namespace,
        str(uuid4()),
        {
            "content": normalized_content,
            "created_at": datetime.now().isoformat(timespec="seconds"),
        },
    )
    return "Memória salva com sucesso."


@tool
def retrieve_memory(
    query: str,
    user_id: Annotated[str, InjectedState("user_id")],
    store: Annotated[BaseStore, InjectedStore],
) -> str:
    """Busca memórias do usuário semanticamente relacionadas ao assunto informado."""
    # Com query, o store embeda a consulta e ordena por similaridade (item.score).
    results = store.search(
        memory_namespace(user_id),
        query=query,
        limit=MAX_RETRIEVED_MEMORIES,
    )
    relevant = [
        item for item in results if item.score is not None and item.score >= MIN_SCORE
    ]
    if not relevant:
        return "Nenhuma memória relevante foi encontrada."
    return "\n".join(f"- {item.value['content']} (score {item.score:.2f})" for item in relevant)


tools = [save_memory, retrieve_memory]
model = ChatGroq(
    model="openai/gpt-oss-120b",
    temperature=0.6,
)
model_with_tools = model.bind_tools(tools)


def call_model(state: AgentState) -> dict[str, list[AnyMessage]]:
    """Lê o histórico da thread e gera a próxima mensagem."""
    messages = [SystemMessage(content=SYSTEM_PROMPT), *state["messages"]]
    return {"messages": [model_with_tools.invoke(messages)]}


def should_continue(state: AgentState) -> Literal["tools", "__end__"]:
    """Envia ao nó de tools quando o modelo solicitar uma ferramenta."""
    last_message = state["messages"][-1]
    if isinstance(last_message, AIMessage) and last_message.tool_calls:
        return "tools"
    return "__end__"


workflow = StateGraph(AgentState)
workflow.add_node("call_model", call_model)
workflow.add_node("tools", ToolNode(tools))
workflow.add_edge(START, "call_model")
workflow.add_conditional_edges("call_model", should_continue)
workflow.add_edge("tools", "call_model")

checkpointer = InMemorySaver()
# index configura a busca semântica: qual função gera os vetores,
# quantas dimensões eles têm e quais campos do valor são indexados.
store = InMemoryStore(
    index={"embed": embed, "dims": EMBEDDING_DIMS, "fields": ["content"]}
)
agent = workflow.compile(checkpointer=checkpointer, store=store)


def seed_memories(user_id: str) -> None:
    """Pré-carrega memórias de exemplo para testar a busca logo de início."""
    for content in (
        "Prefere respostas curtas",
        "Gosta de Python",
        "O nome do usuário é João Pedro",
        "Mora em Curitiba",
        "Tem um cachorro chamado Thor",
    ):
        store.put(
            memory_namespace(user_id),
            str(uuid4()),
            {"content": content, "created_at": datetime.now().isoformat(timespec="seconds")},
        )


def run_chat() -> None:
    """Mantém a thread atual até o usuário enviar uma linha vazia."""
    thread_id = "conversa-local"
    user_id = "usuario-local"
    seed_memories(user_id)
    config: RunnableConfig = {"configurable": {"thread_id": thread_id}}

    while True:
        user_input = input("Input: ").strip()
        if not user_input:
            print("Encerrando a conversa.")
            return

        result = agent.invoke(
            {
                "messages": [HumanMessage(content=user_input)],
                "user_id": user_id,
            },
            config,
        )
        print(result["messages"][-1].content)


if __name__ == "__main__":
    run_chat()
