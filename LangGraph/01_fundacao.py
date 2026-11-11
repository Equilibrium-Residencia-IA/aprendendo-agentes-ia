"""Primeiro passo da migração: um agente mínimo usando LangGraph."""

import os

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from langchain_groq import ChatGroq
from langgraph.graph import END, START, MessagesState, StateGraph


load_dotenv()

if not os.getenv("GROQ_API_KEY"):
    raise RuntimeError("A variável de ambiente GROQ_API_KEY não está configurada.")


model = ChatGroq(
    model="openai/gpt-oss-120b",
    temperature=0.6,
)


def call_model(state: MessagesState) -> dict[str, list]:
    """Envia o histórico atual para o modelo e devolve a nova mensagem."""
    response = model.invoke(state["messages"])
    return {"messages": [response]}


workflow = StateGraph(MessagesState)
workflow.add_node("call_model", call_model)
workflow.add_edge(START, "call_model")
workflow.add_edge("call_model", END)
agent = workflow.compile()


if __name__ == "__main__":
    user_input = input("Input: ").strip()
    if user_input:
        result = agent.invoke(
            {"messages": [HumanMessage(content=user_input)]}
        )
        print(result["messages"][-1].content)
