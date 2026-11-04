
# IMPORTS

from datetime import datetime
import json

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


# DEFINIÇÃO DAS TOOLS DISPONÍVEIS:

tools: list[ChatCompletionToolParam] = [
    {
        # TYPE is always "function"
        "type": "function",
        "function": {
            # NAME is the name of the function on python
            "name": "getTimeNow",

            # DESCRIPTION is what the tool does
            "description": "Retrieves the current time at the user location",

            # PARAMETERS
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
                "additionalProperties": False,
            },

            # STRICT is for validating tool parameters and type-safe function calls
        },
    }
]


def getTimeNow():
    timeNow = datetime.now()
    return timeNow.strftime("%H:%M")


# MAPA ENTRE O NOME DA TOOL E A FUNÇÃO PYTHON QUE SERÁ EXECUTADA

tool_functions = {
    "getTimeNow": getTimeNow,
}

# INICIANDO O AGENTE

print('''
==========================
        RIA AGENT
==========================
''')

historico_mensagens = []

# LOOP AGENTICO

while True:
    # INTERAÇÃO COM O USUÁRIO

    user_input: str = input('Input: ')

    if user_input.strip() == '':
        print('Saindo da interação com o RIA')
        break

    historico_mensagens.append({
        "role": "user",
        "content": user_input,
    })

    # CHAMADA À API

    while True:
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

        message = completion.choices[0].message

        # RETORNO DA TOOL

        if not message.tool_calls:
            # RETORNO E FORMATAÇÃO

            ag_response: str = message.content or ""
            historico_mensagens.append({
                "role": "assistant",
                "content": ag_response,
            })

            console.print(Markdown(ag_response))
            print('\n')

            # PRINT DO TOKEN_USAGE

            if completion.usage is not None:
                print(
                    f"Tokens: {completion.usage.prompt_tokens} usados no prompt, "
                    f"{completion.usage.completion_tokens} na resposta, "
                    f"{completion.usage.total_tokens} no total"
                )
            break

        # O modelo pode solicitar várias tools em uma resposta.
        # Cada resultado é adicionado ao histórico antes da próxima chamada.

        # APPEND DA SOLICITAÇÃO DE TOOL NO HISTÓRICO

        historico_mensagens.append(message.model_dump(exclude_none=True))

        for tool_call in message.tool_calls:
            # IDENTIFICAÇÃO DA TOOL SOLICITADA

            function_name = tool_call.function.name
            function = tool_functions.get(function_name)

            # Esses ifs e o try catch pegam os erros de TOOL CALLING
            # E repassam para o agente entender o que ele fez de errado, e pensar no que fazer a partir disso.

            if function is None:
                historico_mensagens.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": function_name,
                    "content": f"Tool desconhecida: {function_name}",
                })

                # Volta ao loop do agente

                continue

                # raise ValueError(f"Tool desconhecida: {function_name}")


            # LEITURA E VALIDAÇÃO DOS ARGUMENTOS DA TOOL

            try:
                arguments = json.loads(tool_call.function.arguments or "{}")
            except json.JSONDecodeError as error:
                historico_mensagens.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": function_name,
                    "content": f"Argumentos inválidos para a tool {function_name}",
                })

                # Volta ao loop do agente
                continue
            
                #raise ValueError(
                #    f"Argumentos inválidos para a tool {function_name}"
                #) from error

            if not isinstance(arguments, dict) or arguments:
                historico_mensagens.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": function_name,
                    "content": f"A tool {function_name} não aceita argumentos",
                })

                # Volta ao loop do agente

                continue

                # raise ValueError(
                #     f"A tool {function_name} não aceita argumentos"
                # )

            # EXECUÇÃO DA TOOL E APPEND DO RESULTADO NO HISTÓRICO

            historico_mensagens.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "name": function_name,
                "content": function(),
            })