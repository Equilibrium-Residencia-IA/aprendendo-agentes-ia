"""Primeiro passo com LangChain: chat simples com histórico.

Na etapa 01_do_zero você montou a lista de mensagens e chamou a API na mão.
Aqui o ChatGroq faz a chamada e as classes de mensagem substituem os dicts.
"""

import os

from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_groq import ChatGroq

load_dotenv()

if not os.getenv("GROQ_API_KEY"):
    raise RuntimeError("A variável de ambiente GROQ_API_KEY não está configurada.")

model = ChatGroq(model="openai/gpt-oss-120b", temperature=0.6)

if __name__ == "__main__":
    history = [SystemMessage(content="Você é um assistente prestativo e direto.")]
    while True:
        user_input = input("Você: ").strip()
        if user_input.lower() in {"sair", "exit", "quit"}:
            break
        if not user_input:
            continue
        history.append(HumanMessage(content=user_input))
        response: AIMessage = model.invoke(history)
        history.append(response)
        print(f"IA: {response.content}\n")
