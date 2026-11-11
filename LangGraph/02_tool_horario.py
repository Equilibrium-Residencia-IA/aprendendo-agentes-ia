"""Segundo passo: o modelo pode chamar uma tool para consultar o horário."""

import os
from datetime import datetime
from typing import Literal

from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
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


tools = [get_time_now]
tools_by_name = {item.name: item for item in tools}

model = ChatGroq(
    model="openai/gpt-oss-120b",
    temperature=0.6,
).bind_tools(tools)


def call_model(state: MessagesState) -> dict[str, list]:
    """Permite ao modelo responder ou solicitar uma tool."""
    response = model.invoke(state["messages"])
    return {"messages": [response]}


def call_tools(state: MessagesState) -> dict[str, list]:
    """Executa as tools solicitadas pelo modelo."""
    tool_messages = []
    last_message = state["messages"][-1]
    if not isinstance(last_message, AIMessage):
        return {"messages": tool_messages}

    for tool_call in last_message.tool_calls:
        selected_tool = tools_by_name[tool_call["name"]]
        result = selected_tool.invoke(tool_call["args"])
        tool_messages.append(
            ToolMessage(content=result, tool_call_id=tool_call["id"])
        )
    return {"messages": tool_messages}


def should_continue(state: MessagesState) -> Literal["call_tools", "__end__"]:
    """Escolhe entre executar uma tool ou finalizar a resposta."""
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


if __name__ == "__main__":
    user_input = input("Input: ").strip()
    if user_input:
        result = agent.invoke({"messages": [HumanMessage(content=user_input)]})
        print(result["messages"][-1].content)
