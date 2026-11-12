"""Chat no terminal com o A1. Rode a partir da raiz: python 04_diario_emocoes/main.py"""

from langchain_core.messages import AIMessage, HumanMessage

import tools
from agente import agente
from fatos import carregar_fatos
from perfil import atualizar_perfil


def atualizar_perfil_seguro() -> None:
    """Atualiza o perfil sem nunca derrubar o chat: falha de rede só adia a atualização."""
    try:
        print(f"[perfil] {atualizar_perfil(tools.obter_colecao())}")
    except Exception as erro:
        print(f"[perfil] não foi possível atualizar agora ({type(erro).__name__}).")


def montar_saudacao() -> str:
    """Abertura fixa (sem chamar o LLM, para não gastar tokens do Groq a cada abertura)."""
    nome = carregar_fatos().get("nome")
    ola = f"Olá, {nome}." if nome else "Olá."
    return (
        f"{ola} Este é o seu diário: um espaço para registrar o que você viveu e como se sentiu. "
        "Pode falar do que quiser, como trabalho ou estudos, relações, saúde e rotina. "
        "Como foi o seu dia até agora?"
    )


def run_chat() -> None:
    config = {"configurable": {"thread_id": "diario-local"}}
    # Na abertura também: cobre a sessão anterior que terminou sem passar pelo fechamento.
    atualizar_perfil_seguro()
    print("Diário de Emoções. Linha vazia ou 'sair' encerra.\n")
    saudacao = montar_saudacao()
    # Entra no histórico para o agente saber que já perguntou como foi o dia.
    agente.update_state(config, {"messages": [AIMessage(content=saudacao)]}, as_node="model")
    print(f"A1: {saudacao}\n")
    try:
        while True:
            entrada = input("Você: ").strip()
            if not entrada or entrada.lower() in {"sair", "exit", "quit"}:
                break
            resultado = agente.invoke({"messages": [HumanMessage(content=entrada)]}, config)
            print(f"A1: {resultado['messages'][-1].content}\n")
    except (KeyboardInterrupt, EOFError):
        print()
    atualizar_perfil_seguro()
    print("Até a próxima.")


if __name__ == "__main__":
    run_chat()
