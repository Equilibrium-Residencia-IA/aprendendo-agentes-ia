"""Quarto passo: adiciona uma tool de múltipla escolha ao agente."""

import os
from datetime import datetime
from typing import Literal

from dotenv import load_dotenv
from langchain_core.messages import AIMessage, AnyMessage, HumanMessage, ToolMessage
from langchain_core.tools import tool
from langchain_groq import ChatGroq
from langgraph.graph import END, START, MessagesState, StateGraph


load_dotenv()

if not os.getenv("GROQ_API_KEY"):
    raise RuntimeError("A variável de ambiente GROQ_API_KEY não está configurada.")


@tool
def get_time_now() -> str:
    """Retorna o horário local atual no formato HH:MM."""
    return datetime.now().strftime("%H:%M")


@tool
def ask_with_multiple_choice(question: str, choices: list[str]) -> str:
    """Mostra opções ao usuário e retorna a opção escolhida ou uma resposta livre."""
    if not choices:
        raise ValueError("A lista de opções não pode estar vazia.")

    print(f"\nPergunta: {question}")
    for index, choice in enumerate(choices):
        print(f"{index}) {choice}")

    answer = input("Escolha uma opção ou escreva sua resposta: ").strip()
    try:
        choice_index = int(answer)
    except ValueError:
        return f"Resposta do usuário: {answer}"

    if 0 <= choice_index < len(choices):
        return f"Resposta do usuário: {choices[choice_index]}"
    return f"Resposta do usuário: {answer}"


tools = [get_time_now, ask_with_multiple_choice]
tools_by_name = {item.name: item for item in tools}

model = ChatGroq(
    model="openai/gpt-oss-120b",
    temperature=0.6,
).bind_tools(tools)


def call_model(state: MessagesState) -> dict[str, list[AnyMessage]]:
    """Lê o histórico atual e gera a próxima mensagem do modelo."""
    response = model.invoke(state["messages"])
    return {"messages": [response]}


def call_tools(state: MessagesState) -> dict[str, list[ToolMessage]]:
    """Executa todas as tools solicitadas na última mensagem do modelo."""
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
    """Decide se o modelo precisa de uma tool ou pode finalizar o turno."""
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
