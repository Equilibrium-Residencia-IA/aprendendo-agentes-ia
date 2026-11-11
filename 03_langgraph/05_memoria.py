"""Quinto passo: adiciona memória persistente em um arquivo JSON."""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from langchain_core.messages import AIMessage, AnyMessage, HumanMessage, ToolMessage
from langchain_core.tools import tool
from langchain_groq import ChatGroq
from langgraph.graph import START, MessagesState, StateGraph


load_dotenv()

if not os.getenv("GROQ_API_KEY"):
    raise RuntimeError("A variável de ambiente GROQ_API_KEY não está configurada.")


MEMORY_FILE = Path(__file__).with_name("memoria.json")
MAX_RETRIEVED_MEMORIES = 5


def load_memories() -> list[dict[str, str]]:
    """Carrega o arquivo JSON e valida o formato das memórias."""
    if not MEMORY_FILE.exists():
        return []

    try:
        with MEMORY_FILE.open(encoding="utf-8") as file:
            memories = json.load(file)
    except json.JSONDecodeError as error:
        raise RuntimeError(f"Arquivo de memória inválido: {MEMORY_FILE}") from error

    if not isinstance(memories, list) or not all(
        isinstance(memory, dict)
        and isinstance(memory.get("content"), str)
        and isinstance(memory.get("created_at"), str)
        for memory in memories
    ):
        raise RuntimeError(f"Formato de memória inválido: {MEMORY_FILE}")

    return memories


def normalize_words(text: str) -> set[str]:
    """Converte o texto em palavras simples para a busca de memórias."""
    return {
        word.strip(".,!?;:").casefold()
        for word in text.split()
        if len(word.strip(".,!?;:")) > 2
    }


@tool
def save_memory(content: str) -> str:
    """Salva uma preferência ou fato importante para conversas futuras."""
    normalized_content = content.strip()
    if not normalized_content:
        raise ValueError("A memória não pode estar vazia.")

    memories = load_memories()
    if any(
        memory["content"].casefold() == normalized_content.casefold()
        for memory in memories
    ):
        return "Essa memória já está salva."

    memories.append(
        {
            "content": normalized_content,
            "created_at": datetime.now().isoformat(timespec="seconds"),
        }
    )
    with MEMORY_FILE.open("w", encoding="utf-8") as file:
        json.dump(memories, file, ensure_ascii=False, indent=2)
    return "Memória salva com sucesso."


@tool
def retrieve_memory(query: str) -> str:
    """Busca memórias relacionadas ao assunto informado."""
    query_words = normalize_words(query)
    if not query_words:
        return "Nenhuma memória relevante foi encontrada."

    scored_memories = []
    for memory in load_memories():
        score = len(query_words & normalize_words(memory["content"]))
        if score:
            scored_memories.append(
                (score, memory["created_at"], memory["content"])
            )

    scored_memories.sort(key=lambda item: (item[0], item[1]), reverse=True)
    memories = [item[2] for item in scored_memories[:MAX_RETRIEVED_MEMORIES]]
    if not memories:
        return "Nenhuma memória relevante foi encontrada."
    return "\n".join(f"- {memory}" for memory in memories)


tools = [save_memory, retrieve_memory]
tools_by_name = {item.name: item for item in tools}

model = ChatGroq(
    model="openai/gpt-oss-120b",
    temperature=0.6,
).bind_tools(tools)


def call_model(state: MessagesState) -> dict[str, list[AnyMessage]]:
    """Lê o histórico e decide se precisa usar uma tool de memória."""
    response = model.invoke(state["messages"])
    return {"messages": [response]}


def call_tools(state: MessagesState) -> dict[str, list[ToolMessage]]:
    """Executa as tools solicitadas na última mensagem do modelo."""
    last_message = state["messages"][-1]
    if not isinstance(last_message, AIMessage):
        return {"messages": []}

    tool_messages = []
    for tool_call in last_message.tool_calls:
        selected_tool = tools_by_name[tool_call["name"]]
        result = selected_tool.invoke(tool_call["args"])
        tool_messages.append(
            ToolMessage(content=result, tool_call_id=tool_call["id"])
        )
    return {"messages": tool_messages}


def should_continue(state: MessagesState) -> Literal["call_tools", "__end__"]:
    """Continua nas tools quando o modelo fizer uma solicitação."""
    last_message = state["messages"][-1]
    if isinstance(last_message, AIMessage) and last_message.tool_calls:
        return "call_tools"
    return "__end__"


workflow = StateGraph(MessagesState)
workflow.add_node("call_model", call_model)
workflow.add_node("call_tools", call_tools)
workflow.add_edge(START, "call_model")
workflow.add_conditional_edges("call_model", should_continue)
workflow.add_edge("call_tools", "call_model")
agent = workflow.compile()


def run_chat() -> None:
    """Recebe perguntas até o usuário enviar uma linha vazia."""
    history: list[AnyMessage] = []

    while True:
        user_input = input("Input: ").strip()
        if not user_input:
            print("Encerrando a conversa.")
            return

        history.append(HumanMessage(content=user_input))
        result = agent.invoke({"messages": history})
        history = result["messages"]
        print(history[-1].content)


if __name__ == "__main__":
    run_chat()
