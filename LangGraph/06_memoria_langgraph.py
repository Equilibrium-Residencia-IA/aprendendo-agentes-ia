"""Sexto passo: usa checkpointer e store nativos do LangGraph."""

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


load_dotenv()

if not os.getenv("GROQ_API_KEY"):
    raise RuntimeError("A variável de ambiente GROQ_API_KEY não está configurada.")


MAX_RETRIEVED_MEMORIES = 5
SYSTEM_PROMPT = """Você é um assistente com memória de longo prazo.
Quando o usuário pedir para lembrar, salvar ou guardar uma preferência ou fato,
use obrigatoriamente a ferramenta save_memory antes de responder.
Quando o usuário perguntar se você lembra algo ou pedir uma preferência salva,
use obrigatoriamente a ferramenta retrieve_memory.
Não diga que salvou ou encontrou uma memória sem executar a ferramenta.
Responda em português e seja claro."""


class AgentState(MessagesState):
    """Estado da conversa, incluindo o identificador do usuário."""

    user_id: str


def memory_namespace(user_id: str) -> tuple[str, str]:
    """Define o namespace que separa as memórias de cada usuário."""
    return (user_id, "memories")


def normalize_words(text: str) -> set[str]:
    """Converte o texto em palavras simples para a busca de memórias."""
    return {
        word.strip(".,!?;:").casefold()
        for word in text.split()
        if len(word.strip(".,!?;:")) > 2
    }


def save_memory_value(
    content: str,
    user_id: str,
    store: BaseStore,
) -> str:
    """Salva uma memória no store do usuário."""
    normalized_content = content.strip()
    if not normalized_content:
        raise ValueError("A memória não pode estar vazia.")

    namespace = memory_namespace(user_id)
    memories = store.search(namespace, limit=100)
    if any(
        item.value.get("content", "").casefold() == normalized_content.casefold()
        for item in memories
    ):
        return "Essa memória já está salva."

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
def save_memory(
    content: str,
    user_id: Annotated[str, InjectedState("user_id")],
    store: Annotated[BaseStore, InjectedStore],
) -> str:
    """Salva uma preferência ou fato importante para conversas futuras."""
    return save_memory_value(content, user_id, store)


@tool
def retrieve_memory(
    query: str,
    user_id: Annotated[str, InjectedState("user_id")],
    store: Annotated[BaseStore, InjectedStore],
) -> str:
    """Busca memórias do usuário relacionadas ao assunto informado."""
    query_words = normalize_words(query)
    if not query_words:
        return "Nenhuma memória relevante foi encontrada."

    scored_memories = []
    for item in store.search(memory_namespace(user_id), limit=100):
        content = item.value.get("content")
        created_at = item.value.get("created_at", "")
        if not isinstance(content, str) or not isinstance(created_at, str):
            continue

        score = len(query_words & normalize_words(content))
        if score:
            scored_memories.append((score, created_at, content))

    scored_memories.sort(key=lambda item: (item[0], item[1]), reverse=True)
    memories = [item[2] for item in scored_memories[:MAX_RETRIEVED_MEMORIES]]
    if not memories:
        return "Nenhuma memória relevante foi encontrada."
    return "\n".join(f"- {memory}" for memory in memories)


tools = [save_memory, retrieve_memory]
model = ChatGroq(
    model="openai/gpt-oss-120b",
    temperature=0.6,
)
model_with_tools = model.bind_tools(tools)


def memory_intent(user_input: str) -> Literal["save", "retrieve", "none"]:
    """Identifica pedidos explícitos de salvar ou consultar memórias."""
    text = user_input.casefold()
    save_words = (
        "lembre",
        "memorize",
        "guardar",
        "guarde",
        "salve",
        "prefiro",
        "gosto de",
        "meu nome é",
    )
    retrieve_words = (
        "você lembra",
        "qual é minha",
        "qual minha",
        "o que você sabe sobre mim",
        "minha preferência",
    )
    if any(phrase in text for phrase in retrieve_words):
        return "retrieve"
    if any(phrase in text for phrase in save_words):
        return "save"
    return "none"


def memory_content(user_input: str) -> str:
    """Remove o comando de memória e preserva somente o fato informado."""
    normalized_input = user_input.strip()
    for prefix in ("lembre que ", "memorize que ", "guarde que ", "salve que "):
        if normalized_input.casefold().startswith(prefix):
            return normalized_input[len(prefix):].strip()
    return normalized_input


def call_model(state: AgentState) -> dict[str, list[AnyMessage]]:
    """Lê o histórico da thread e gera a próxima mensagem."""
    messages = [SystemMessage(content=SYSTEM_PROMPT), *state["messages"]]
    last_human_message = next(
        (
            message
            for message in reversed(state["messages"])
            if isinstance(message, HumanMessage)
        ),
        None,
    )
    selected_model = model_with_tools
    intent: Literal["save", "retrieve", "none"] = "none"
    if (
        last_human_message is not None
        and isinstance(last_human_message.content, str)
    ):
        intent = memory_intent(last_human_message.content)

    response = selected_model.invoke(messages)
    if (
        intent == "save"
        and not response.tool_calls
        and last_human_message is not None
        and isinstance(last_human_message.content, str)
    ):
        result = save_memory_value(
            memory_content(last_human_message.content),
            state["user_id"],
            store,
        )
        response = AIMessage(content=result)
    return {"messages": [response]}


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
store = InMemoryStore()
agent = workflow.compile(checkpointer=checkpointer, store=store)


def run_chat() -> None:
    """Mantém a thread atual até o usuário enviar uma linha vazia."""
    thread_id = "conversa-local"
    user_id = "usuario-local"
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
