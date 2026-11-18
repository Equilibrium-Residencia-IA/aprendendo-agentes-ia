"""Chat de terminal do agente final.

Uso: python 04_agente_final/main.py [--user joao] [--thread NOME]
Clientes de demonstração com pedidos: joao, maria. Qualquer outro nome funciona (sem pedidos).
Comandos: /novo (nova conversa), /memorias, /sair
"""

import argparse
import uuid

from langchain_core.messages import HumanMessage
from langgraph.types import Command

import knowledge
import memory
from graph import build_agent


def run_turn(agent, config: dict, payload) -> None:
    """Executa um turno, mostrando as tools chamadas; trata a aprovação de chamados."""
    while True:
        interrupted = None
        for chunk in agent.stream(payload, config, stream_mode="updates"):
            for node, update in chunk.items():
                if node == "__interrupt__":
                    interrupted = update[0].value
                    continue
                for message in (update or {}).get("messages", []):
                    for call in getattr(message, "tool_calls", None) or []:
                        print(f"  · {call['name']}({call['args']})")
                    if node == "agent" and message.content and not message.tool_calls:
                        print(f"\n{message.content}\n")
        if interrupted is None:
            return
        print(f"\n  Abrir chamado? Assunto: {interrupted['subject']}")
        print(f"  Descrição: {interrupted['description']}")
        approved = input("  Confirmar (s/N): ").strip().lower() in {"s", "sim", "y"}
        payload = Command(resume=approved)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--user", default="joao")
    parser.add_argument("--thread", default=None)
    args = parser.parse_args()

    print(knowledge.sync_index(), "\n")
    agent = build_agent()
    thread = args.thread or f"{args.user}-principal"

    print(f"Atendimento Loja Aurora — cliente '{args.user}', conversa '{thread}'. Linha vazia ou /sair encerra.\n")
    while True:
        text = input("Você: ").strip()
        if not text or text == "/sair":
            return
        if text == "/novo":
            thread = f"{args.user}-{uuid.uuid4().hex[:6]}"
            print(f"(nova conversa: {thread})")
            continue
        if text == "/memorias":
            print("\n".join(f"- {m}" for m in memory.list_memories(args.user)) or "(vazio)")
            continue
        config = {"configurable": {"thread_id": thread}}
        run_turn(agent, config, {"messages": [HumanMessage(text)], "user_id": args.user})


if __name__ == "__main__":
    main()
