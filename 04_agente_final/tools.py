"""Tools do agente de suporte: políticas (RAG), pedidos, chamados e memória.

O `user_id` nunca é argumento escolhido pelo modelo: vem do estado do grafo
(`InjectedState`), então um cliente não consegue consultar pedidos de outro.
"""

from typing import Annotated

from langchain_core.tools import tool
from langgraph.prebuilt import InjectedState
from langgraph.types import interrupt

import knowledge
import memory
import orders

UserId = Annotated[str, InjectedState("user_id")]


def _format_order(order: dict) -> str:
    lines = [
        f"Pedido {order['id']}: {', '.join(order['items'])}",
        f"- status: {order['status']}",
        f"- total: R$ {order['total']:.2f}",
        f"- frete: {order['shipping']} (região {order['region']})",
        f"- feito há {order['ordered_days_ago']} dia(s)",
    ]
    if order.get("delivered_days_ago") is not None:
        lines.append(f"- entregue há {order['delivered_days_ago']} dia(s)")
    if order.get("tracking"):
        lines.append(f"- rastreio: {order['tracking']}")
    return "\n".join(lines)


@tool
def search_docs(query: str) -> str:
    """Busca nas políticas da loja (devolução, reembolso, frete, entrega e prazos).

    Use para qualquer pergunta sobre regras. Cada trecho vem com a fonte entre colchetes
    ([arquivo#trecho]); cite-a exatamente assim na resposta.
    """
    hits = knowledge.search_docs(query)
    if not hits:
        return "Nada encontrado nas políticas da loja para essa pergunta."
    return "\n\n".join(f"[{chunk_id}] {text}" for chunk_id, _score, text in hits)


@tool
def get_order_status(order_id: str, user_id: UserId) -> str:
    """Status e detalhes de um pedido do cliente atual, pelo número (ex.: A-1001)."""
    order = orders.get_order(user_id, order_id)
    return _format_order(order) if order else f"Pedido {order_id} não encontrado para este cliente."


@tool
def list_my_orders(user_id: UserId) -> str:
    """Lista os pedidos do cliente atual, com o status de cada um."""
    found = orders.list_orders(user_id)
    if not found:
        return "Este cliente não tem pedidos."
    return "\n".join(
        f"- {o['id']}: {', '.join(o['items'])} ({o['status']})" for o in found
    )


@tool
def check_return_eligibility(order_id: str, user_id: UserId, defect: bool = False) -> str:
    """Confere só o PRAZO de devolução de um pedido do cliente atual.

    O prazo conta a partir do recebimento: 7 dias corridos em geral, 90 dias se o produto
    tem defeito (`defect=True`). Não avalia as condições do produto (embalagem, uso,
    personalização): para isso, consulte também search_docs.
    """
    order = orders.get_order(user_id, order_id)
    if order is None:
        return f"Pedido {order_id} não encontrado para este cliente."
    days = order.get("delivered_days_ago")
    if days is None:
        return (
            f"O pedido {order['id']} ainda não foi entregue (status: {order['status']}). "
            "O prazo de devolução só começa a contar a partir do recebimento."
        )
    window = orders.DEFECT_WINDOW_DAYS if defect else orders.RETURN_WINDOW_DAYS
    kind = "com defeito" if defect else "por arrependimento"
    if days <= window:
        return (
            f"Dentro do prazo ({kind}): entregue há {days} dia(s), prazo de {window} dias "
            f"(restam {window - days})."
        )
    return f"Fora do prazo ({kind}): entregue há {days} dia(s), prazo de {window} dias."


@tool
def open_support_ticket(
    subject: str, description: str, user_id: UserId, order_id: str | None = None
) -> str:
    """Abre um chamado para a equipe humana, depois de o cliente confirmar.

    Use só quando o cliente pedir para falar com a equipe ou o problema não for resolvível
    pelas outras ferramentas. Resuma o caso em `description`.
    """
    approved = interrupt({"subject": subject, "description": description, "order_id": order_id})
    if not approved:
        return "O cliente não confirmou; nenhum chamado foi aberto."
    ticket_id = orders.create_ticket(user_id, subject, description, order_id)
    return f"Chamado {ticket_id} aberto. A equipe responde por e-mail."


@tool
def save_memory(content: str, user_id: UserId) -> str:
    """Salva um fato durável sobre o cliente (preferência, nome, contexto).

    Não salve dados de pagamento, senhas nem conteúdo de pedidos.
    """
    return memory.remember(user_id, content)


@tool
def forget_memory(memory_id: str, user_id: UserId) -> str:
    """Remove uma memória do cliente pelo id mostrado por save_memory (ex.: 3fa85f64)."""
    return memory.forget(user_id, memory_id)


tools = [
    search_docs,
    get_order_status,
    list_my_orders,
    check_return_eligibility,
    open_support_ticket,
    save_memory,
    forget_memory,
]
