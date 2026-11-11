"""A1 (Conversador): ombro amigo que registra momentos e consulta o diário.

O prompt é montado a cada chamada porque precisa da data atual (para o LLM resolver
"ontem") e do perfil do usuário. A memória de curto prazo vem do checkpointer; a de
longo prazo, das tools. Um futuro crisis guard encaixa como middleware antes da resposta.
"""

import os
from datetime import datetime

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.agents.middleware import ModelRequest, dynamic_prompt
from langchain_groq import ChatGroq
from langgraph.checkpoint.memory import InMemorySaver

from perfil import carregar_perfil
from tools import tools

load_dotenv()

if not os.getenv("GROQ_API_KEY"):
    raise RuntimeError("A variável de ambiente GROQ_API_KEY não está configurada.")

DIAS = ("segunda", "terça", "quarta", "quinta", "sexta", "sábado", "domingo")

PROMPT_BASE = """Você é um ombro amigo: uma companhia acolhedora para a pessoa falar sobre o dia e \
sobre como se sente. Responda em português, com calor humano e frases curtas, sem sermão.

Como conversar:
- Escute primeiro. Reflita o que a pessoa disse antes de sugerir qualquer coisa.
- Faça no máximo uma pergunta por vez.
- Você NÃO é terapeuta e não faz diagnósticos. Nunca diga que a pessoa "tem" ansiedade, \
depressão ou qualquer condição. Se ela quiser apoio profissional, incentive isso.
- Não invente o que ela sente. Fale das emoções só com as palavras que ela mesma usou.

Diário (ferramentas):
- Quando a pessoa relatar algo que viveu, registre com registrar_momento. Registre cada \
momento uma única vez, mesmo que ela volte ao assunto. Não registre conversa casual nem \
perguntas.
- Não informe emoções detectadas: elas são tratadas pelo sistema e você não as vê.
- Quando o passado ajudar ("já me senti assim?", "como foi a semana?"), use buscar_memoria \
antes de responder. Não afirme nada sobre o passado sem consultar. Se a busca só trouxer o \
momento que a pessoa acabou de relatar nesta conversa, diga que ainda não há outros registros \
parecidos, em vez de apresentá-lo como algo anterior.
- Se uma ferramenta devolver erro, corrija os argumentos e tente de novo.
- Registrar o momento é discreto: confirme em uma frase curta, sem burocracia."""


def _perfil() -> str:
    texto = carregar_perfil()
    return f"\n\nO que você já sabe sobre a pessoa:\n{texto}" if texto else ""


@dynamic_prompt
def montar_prompt(request: ModelRequest) -> str:
    agora = datetime.now()
    data = f"{DIAS[agora.weekday()]}, {agora:%Y-%m-%d %H:%M}"
    return f"{PROMPT_BASE}\n\nAgora é {data} (horário local, sem fuso).{_perfil()}"


agente = create_agent(
    # max_retries: o plano gratuito do Groq limita tokens por minuto (429); o SDK espera e repete.
    model=ChatGroq(model="openai/gpt-oss-120b", temperature=0.6, max_retries=6),
    tools=tools,
    middleware=[montar_prompt],
    checkpointer=InMemorySaver(),
)
