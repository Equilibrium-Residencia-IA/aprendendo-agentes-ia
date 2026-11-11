"""Décimo primeiro passo: RAG com limiar de similaridade e citação de fontes.

Diferenças em relação ao 10:
- search_docs descarta chunks abaixo de MIN_DOC_SCORE e devolve "nada encontrado"
  quando nenhum passa (a recusa vem da busca, não só do modelo);
- o prompt exige citar a fonte de cada informação no formato [arquivo#chunk].
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

TOP_K = 3
# Calibrado com consultas reais: perguntas cobertas pelos documentos tiveram
# score >= 0.47 e as não cobertas (boleto, telefone, senha...) ficaram <= 0.34.
MIN_DOC_SCORE = 0.40

SYSTEM_PROMPT = """Você é o assistente de atendimento da Loja Aurora, com memória de longo prazo.
Para qualquer pergunta sobre a loja (devolução, reembolso, frete, entrega, prazos),
use obrigatoriamente a ferramenta search_docs e responda SOMENTE com base no que ela retornar.
Cite a fonte de cada informação ao final da frase, no formato [arquivo#chunk],
usando exatamente o identificador que a ferramenta mostrou.
Se a ferramenta disser que nada foi encontrado, diga que não tem essa informação
e sugira falar com suporte@aurora.example. Nunca complete com conhecimento próprio.
Para pedidos de lembrar algo ou perguntas pessoais do usuário, use save_memory e retrieve_memory.
Responda em português e seja claro."""


@tool
def search_docs(
    query: str,
    store: Annotated[BaseStore, InjectedStore],
) -> str:
    """Busca nos documentos da loja trechos relacionados à pergunta."""
    results = store.search(passo_09.DOCS_NAMESPACE, query=query, limit=TOP_K)
    relevant = [item for item in results if item.score is not None and item.score >= MIN_DOC_SCORE]
    if not relevant:
        return "Nenhum trecho relevante encontrado nos documentos."
    return "\n\n".join(
        f"[{item.key}] (score {item.score:.2f})\n{item.value['content']}" for item in relevant
    )


tools = [search_docs, passo_08.save_memory, passo_08.retrieve_memory]
model_with_tools = passo_08.model.bind_tools(tools)


def call_model(state: passo_08.AgentState) -> dict:
    messages = [SystemMessage(content=SYSTEM_PROMPT), *state["messages"]]
    return {"messages": [model_with_tools.invoke(messages)]}


workflow = StateGraph(passo_08.AgentState)
workflow.add_node("call_model", call_model)
workflow.add_node("tools", ToolNode(tools))
workflow.add_edge(START, "call_model")
workflow.add_conditional_edges("call_model", passo_08.should_continue)
workflow.add_edge("tools", "call_model")

store = passo_08.store
agent = workflow.compile(checkpointer=InMemorySaver(), store=store)


def run_chat() -> None:
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
