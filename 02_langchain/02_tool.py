"""Segundo passo: um agente com tool usando create_agent.

Compare com 01_do_zero/02_tool_calling.py e 03_langgraph/02_tool_horario.py:
o loop "modelo -> tool -> modelo" que você escreveu à mão (ou como grafo)
está todo dentro de create_agent.
"""

import os
from datetime import datetime

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage
from langchain_core.tools import tool
from langchain_groq import ChatGroq

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
)

if __name__ == "__main__":
    user_input = input("Input: ").strip()
    if user_input:
        result = agent.invoke({"messages": [HumanMessage(content=user_input)]})
        for message in result["messages"]:
            message.pretty_print()
