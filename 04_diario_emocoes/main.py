"""Chat no terminal com o A1. Rode a partir da raiz: python 04_diario_emocoes/main.py"""

from langchain_core.messages import HumanMessage

from agente import agente


def run_chat() -> None:
    config = {"configurable": {"thread_id": "diario-local"}}
    print("Diário de Emoções. Linha vazia ou 'sair' encerra.\n")
    while True:
        entrada = input("Você: ").strip()
        if not entrada or entrada.lower() in {"sair", "exit", "quit"}:
            print("Até a próxima.")
            return
        resultado = agente.invoke({"messages": [HumanMessage(content=entrada)]}, config)
        print(f"A1: {resultado['messages'][-1].content}\n")


if __name__ == "__main__":
    run_chat()
