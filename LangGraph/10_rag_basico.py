"""Décimo passo: RAG básico. O agente busca chunks de documentos e responde com base neles.

Reaproveita do 08 o estado, o modelo, as tools de memória e o store (com embeddings),
e do 09 o carregamento e a indexação de documentos. Os documentos ficam no mesmo
store da memória, mas em outro namespace ("docs"), então não se misturam.
"""

from importlib import import_module
from typing import Annotated

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import START, StateGraph
from langgraph.prebuilt import InjectedStore, ToolNode
from langgraph.store.base import BaseStore

passo_08 = import_module("08_busca_semantica")
passo_09 = import_module("09_documentos")

TOP_K = 3  # quantos chunks entram no contexto de cada busca

SYSTEM_PROMPT = """Você é o assistente de atendimento da Loja Aurora, com memória de longo prazo.
Para qualquer pergunta sobre a loja (devolução, reembolso, frete, entrega, prazos),
use obrigatoriamente a ferramenta search_docs e responda SOMENTE com base no que ela retornar.
Para pedidos de lembrar algo ou perguntas pessoais do usuário, use save_memory e retrieve_memory.
Não invente informações. Responda em português e seja claro."""


@tool
def search_docs(
    query: str,
    store: Annotated[BaseStore, InjectedStore],
) -> str:
    """Busca nos documentos da loja trechos relacionados à pergunta."""
    results = store.search(passo_09.DOCS_NAMESPACE, query=query, limit=TOP_K)
    if not results:
        return "Nenhum trecho encontrado nos documentos."
    # Cada trecho vai com a fonte, para o modelo saber de onde veio a informação.
    return "\n\n".join(
        f"[{item.value['source']}] (score {item.score:.2f})\n{item.value['content']}"
        for item in results
    )


tools = [search_docs, passo_08.save_memory, passo_08.retrieve_memory]
model_with_tools = passo_08.model.bind_tools(tools)


def call_model(state: passo_08.AgentState) -> dict:
    """Mesmo nó do 08, mas com o prompt e as tools do RAG."""
    messages = [SystemMessage(content=SYSTEM_PROMPT), *state["messages"]]
    return {"messages": [model_with_tools.invoke(messages)]}


workflow = StateGraph(passo_08.AgentState)
workflow.add_node("call_model", call_model)
workflow.add_node("tools", ToolNode(tools))
workflow.add_edge(START, "call_model")
workflow.add_conditional_edges("call_model", passo_08.should_continue)
workflow.add_edge("tools", "call_model")

# Reaproveita o store do 08, que já tem o índice de embeddings configurado.
store = passo_08.store
agent = workflow.compile(checkpointer=InMemorySaver(), store=store)


def run_chat() -> None:
    """Indexa os documentos e mantém a conversa até uma linha vazia."""
    user_id = "usuario-local"
    passo_08.seed_memories(user_id)
    total = passo_09.index_documents(store, passo_09.load_documents(passo_09.DOCS_DIR))
    print(f"{total} chunks de documentos indexados.\n")

    config: RunnableConfig = {"configurable": {"thread_id": "conversa-rag"}}
    while True:
        user_input = input("Input: ").strip()
        if not user_input:
            print("Encerrando a conversa.")
            return
        result = agent.invoke(
            {"messages": [HumanMessage(content=user_input)], "user_id": user_id},
            config,
        )
        print(result["messages"][-1].content, "\n")


if __name__ == "__main__":
    run_chat()
