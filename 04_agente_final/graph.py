"""O grafo: recall (memória) -> agent <-> tools, com checkpoint em SQLite."""

import sqlite3
from datetime import datetime
from typing import Literal

from langchain_core.messages import AIMessage, AnyMessage, HumanMessage, SystemMessage, trim_messages
from langchain_groq import ChatGroq
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode

import memory
from config import CHECKPOINT_DB, MAX_HISTORY_MESSAGES, MODEL_NAME, MODEL_TEMPERATURE
from tools import tools

SYSTEM_PROMPT = """Você é a assistente de atendimento da Loja Aurora. Responda em português, de forma clara e objetiva.

Regras:
- Políticas (devolução, reembolso, frete, entrega, prazos): use search_docs e responda SOMENTE com o que ela retornar.
  Cite a fonte ao final de cada informação, no formato [arquivo#chunk], exatamente como a ferramenta mostrou.
  Se nada for encontrado, diga que não tem a informação e ofereça abrir um chamado. Nunca invente políticas.
- Dados de pedido: use get_order_status / list_my_orders. Nunca invente status, datas ou valores.
- Pergunta "posso devolver?": combine check_return_eligibility (prazo) com search_docs (condições).
- Chamado: só use open_support_ticket quando o cliente quiser falar com a equipe ou o problema não for
  resolvível por você. Resuma o caso no chamado.
- Memória: quando o cliente contar algo durável sobre si (preferência, nome, contexto), chame save_memory.
  Não salve dados de pagamento, senhas nem o conteúdo de pedidos (isso já está no sistema).
  Se o save_memory listar memórias parecidas que ficaram obsoletas (ex.: o cliente mudou de cidade),
  remova-as com forget_memory. Se o cliente pedir para esquecer algo, use forget_memory.
- Os "Fatos conhecidos" abaixo vêm da memória; use-os naturalmente, sem dizer que consultou uma memória.

Hoje é {today}. Cliente: {user_id}.

Fatos conhecidos sobre o cliente:
{facts}"""


class AgentState(MessagesState):
    user_id: str
    facts: list[str]


model = ChatGroq(model=MODEL_NAME, temperature=MODEL_TEMPERATURE).bind_tools(tools)


def recall(state: AgentState) -> dict:
    """Busca memórias relevantes à última fala do cliente antes de o modelo responder."""
    last_human = next(
        (m for m in reversed(state["messages"]) if isinstance(m, HumanMessage)), None
    )
    query = last_human.content if last_human and isinstance(last_human.content, str) else ""
    return {"facts": memory.recall(state["user_id"], query) if query else []}


def call_model(state: AgentState) -> dict[str, list[AnyMessage]]:
    facts = "\n".join(f"- {f}" for f in state.get("facts", [])) or "(nenhum relevante)"
    system = SystemMessage(
        SYSTEM_PROMPT.format(
            today=datetime.now().strftime("%d/%m/%Y"), user_id=state["user_id"], facts=facts
        )
    )
    # O checkpoint guarda a conversa inteira; o modelo só vê as mensagens mais recentes.
    recent = trim_messages(
        state["messages"],
        strategy="last",
        max_tokens=MAX_HISTORY_MESSAGES,
        token_counter=len,
        start_on="human",
        include_system=False,
    )
    return {"messages": [model.invoke([system, *recent])]}


def should_continue(state: AgentState) -> Literal["tools", "__end__"]:
    last = state["messages"][-1]
    return "tools" if isinstance(last, AIMessage) and last.tool_calls else "__end__"


def build_agent():
    workflow = StateGraph(AgentState)
    workflow.add_node("recall", recall)
    workflow.add_node("agent", call_model)
    workflow.add_node("tools", ToolNode(tools))
    workflow.add_edge(START, "recall")
    workflow.add_edge("recall", "agent")
    workflow.add_conditional_edges("agent", should_continue)
    workflow.add_edge("tools", "agent")
    connection = sqlite3.connect(CHECKPOINT_DB, check_same_thread=False)
    return workflow.compile(checkpointer=SqliteSaver(connection))
