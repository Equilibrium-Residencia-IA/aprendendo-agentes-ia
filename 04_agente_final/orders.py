"""Pedidos e chamados. Os pedidos são dados de demonstração (orders.json)."""

import json
from datetime import datetime
from uuid import uuid4

from config import ORDERS_FILE, TICKETS_FILE

# Prazos de devolução da política (data/docs/politica_reembolso.md).
# Se a política mudar, atualize aqui também.
RETURN_WINDOW_DAYS = 7
DEFECT_WINDOW_DAYS = 90


def _load_orders(user_id: str) -> list[dict]:
    data = json.loads(ORDERS_FILE.read_text(encoding="utf-8"))
    return data.get(user_id, [])


def get_order(user_id: str, order_id: str) -> dict | None:
    """Só devolve pedidos do próprio usuário: o user_id vem do estado, não do modelo."""
    for order in _load_orders(user_id):
        if order["id"].casefold() == order_id.strip().casefold():
            return order
    return None


def list_orders(user_id: str) -> list[dict]:
    return _load_orders(user_id)


def create_ticket(user_id: str, subject: str, description: str, order_id: str | None) -> str:
    tickets = json.loads(TICKETS_FILE.read_text()) if TICKETS_FILE.exists() else []
    ticket_id = f"T-{uuid4().hex[:6].upper()}"
    tickets.append(
        {
            "id": ticket_id,
            "user_id": user_id,
            "order_id": order_id,
            "subject": subject,
            "description": description,
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "status": "aberto",
        }
    )
    TICKETS_FILE.write_text(json.dumps(tickets, ensure_ascii=False, indent=2), encoding="utf-8")
    return ticket_id
