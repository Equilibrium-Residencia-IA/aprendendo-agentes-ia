
# IMPORTS

from datetime import datetime

import groq
import os
from dotenv import load_dotenv
from groq.types.chat import ChatCompletionToolParam

from rich.console import Console
from rich.markdown import Markdown

# CARREGAR AMBIENTE

load_dotenv()

console = Console()

api_key: str | None = os.getenv("GROQ_API_KEY")

if api_key is None:
    print('API NÃO CONFIGURADA')

client: groq.Groq = groq.Groq(api_key=api_key)

historico_mensagens = []

# DEFINIÇÃO DAS TOOLS DISPONÍVEIS:

tools: list[ChatCompletionToolParam] = [
    {
        "type": "function",
        "function": {
            "name": "getTimeNow",
            "description": "Retrieves the current time at the user location",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
                "additionalProperties": False,
            },
        },
    }
]
    


def getTimeNow():
    timeNow = datetime.now()
    return timeNow.strftime("%H:%M")

# INTERAÇÃO COM O USUÁRIO

user_input: str = input('Input: ')

if (user_input.strip() == ''):
    raise Exception("Insira uma mensagem válida.")

historico_mensagens.append({
    "role": "user",
    "content": user_input
})

# CHAMADA À API

completion = client.chat.completions.create(

    # HISTÓRICO DE MENSAGENS (substitui o prompt e serve como memória):

    messages=historico_mensagens,

    # CONFIGS DO MODELO:

    model="openai/gpt-oss-120b",
    reasoning_effort="medium",
    temperature=0.6,
    max_completion_tokens=1024,
    top_p=0.8,

    # TOOLS:

    tools=tools,
    tool_choice="auto",

)

# RETORNO E FORMATAÇÃO

ag_response: str = completion.choices[0].message.content or ""


markdown = Markdown(ag_response)
console.print(markdown)
print('\n')

# PRINT DO TOKEN_USAGE 

if completion.usage is not None:
    print(
        f"Tokens: {completion.usage.prompt_tokens} usados no prompt, "
        f"{completion.usage.completion_tokens} na resposta, "
        f"{completion.usage.total_tokens} no total"
    )
print(f'Finish Reason: {completion.choices[0].finish_reason}')
print(f'Tool Calls: {completion.choices[0].message.tool_calls}')

# APPEND NO HISTÓRICO DE MENSAGENS (Memória do agente)

historico_mensagens.append({"role": "assistant", "content": ag_response})
