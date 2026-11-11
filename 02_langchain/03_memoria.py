"""Terceiro passo: histórico entre turnos com checkpointer.

create_agent é construído sobre o LangGraph, então a memória de curto prazo
vem do mesmo checkpointer que você verá em 03_langgraph/06_memoria_langgraph.py.
O thread_id identifica a conversa.
"""

import os
from datetime import datetime

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage
from langchain_core.tools import tool
from langchain_groq import ChatGroq
from langgraph.checkpoint.memory import InMemorySaver

load_dotenv()

if not os.getenv("GROQ_API_KEY"):
    raise RuntimeError("A variável de ambiente GROQ_API_KEY não está configurada.")


@tool
def get_time_now() -> str:
    """Retorna o horário local atual no formato HH:MM."""
    return datetime.now().strftime("%H:%M")


agent = create_agent(
    model=ChatGroq(model="openai/gpt-oss-120b", temperature=0.6),
    tools=[get_time_now],
    system_prompt="Você é um assistente prestativo e direto.",
    checkpointer=InMemorySaver(),
)

if __name__ == "__main__":
    config = {"configurable": {"thread_id": "conversa-1"}}
    while True:
        user_input = input("Você: ").strip()
        if user_input.lower() in {"sair", "exit", "quit"}:
            break
        if not user_input:
            continue
        result = agent.invoke({"messages": [HumanMessage(content=user_input)]}, config)
        print(f"IA: {result['messages'][-1].content}\n")
