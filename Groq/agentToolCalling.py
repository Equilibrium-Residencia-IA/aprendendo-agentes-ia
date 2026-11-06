
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
    raise RuntimeError("A variável de ambiente GROQ_API_KEY não está configurada.")

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
    },
    {
        # TYPE is always "function"
        "type": "function",
        "function": {
            # NAME is the name of the function on python
            "name": "askWithMultipleChoice",

            # DESCRIPTION is what the tool does
            "description": "Ask a question, with some choices to the user to choose, the user can also write his own answer",

            # PARAMETERS
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": "The question that you want to be answered by the user",
                    },
                    "choices": {
                        "type": "array",
                        "items": {
                            "type": "string",
                        },
                        "description": "Answers options list",
                    },
                },
                "required": ["question", "choices"],
                "additionalProperties": False,
            },

            # STRICT is for validating tool parameters and type-safe function calls
            "strict": True,
        },
    }
]


def getTimeNow() -> str:
    time_now = datetime.now()
    return time_now.strftime("%H:%M")

def askWithMultipleChoice(question: str, choices: list[str]) -> str:
    print(f"Pergunta: {question}")
    print("---------------------")
    print("Selecione a resposta:")
    for i, choice in enumerate(choices):
        print(f"{i}) {choice}")
    print("---------------------")

    answer = input("> ")

    try:
        choice_index = int(answer)
    except ValueError:
        return (
            f"Pergunta recebida pelo usuário: {question}; "
            f"Resposta do usuário: {answer}"
        )

    if 0 <= choice_index < len(choices):
        return (
            f"Pergunta recebida pelo usuário: {question}; "
            f"Resposta do usuário: {choices[choice_index]}"
        )

    return (
        f"Pergunta recebida pelo usuário: {question}; "
        f"Resposta do usuário: {answer}"
    )


# MAPA ENTRE O NOME DA TOOL E A FUNÇÃO PYTHON QUE SERÁ EXECUTADA

tool_functions = {
    "getTimeNow": getTimeNow,
    "askWithMultipleChoice": askWithMultipleChoice,
}

# INICIANDO O AGENTE

print('''
==========================
        R・IA AGENT
==========================
''')

historico_mensagens = []
MAX_ITERATIONS = 6
MAX_TOOL_CALLS = 10
MAX_COMPLETION_TOKENS = 4096

# LOOP AGENTICO

while True:
    # INTERAÇÃO COM O USUÁRIO

    user_input: str = input('Input: ')

    if user_input.strip() == '':
        print('Saindo da interação com o RIA')
        break

    turn_start_index = len(historico_mensagens)
    historico_mensagens.append({
        "role": "user",
        "content": user_input,
    })

    # CHAMADA À API

    iterations = 0
    tool_calls_count = 0
    completed = False
    total_cost = 0

    while iterations < MAX_ITERATIONS:
        iterations += 1
        
        completion = client.chat.completions.create(

            # HISTÓRICO DE MENSAGENS (substitui o prompt e serve como memória):

            messages=historico_mensagens,

            # CONFIGS DO MODELO:

            model="openai/gpt-oss-120b",
            reasoning_effort="medium",
            temperature=0.6,
            max_completion_tokens=MAX_COMPLETION_TOKENS,
            top_p=0.8,

            # TOOLS:

            tools=tools,
            tool_choice="auto",
        )

        message = completion.choices[0].message
        finish_reason = completion.choices[0].finish_reason

        # RETORNO DA TOOL

        match finish_reason:
            case "stop":

                # RETORNO E FORMATAÇÃO
                completed = True

                ag_response: str = message.content or ""
                historico_mensagens.append({
                    "role": "assistant",
                    "content": ag_response,
                })

                console.print(Markdown(ag_response))
                print('\n')

                # PRINT DO TOKEN_USAGE

                if completion.usage is not None:
                    total_cost += completion.usage.total_tokens
                    print(
                        f"Tokens: {completion.usage.prompt_tokens} usados no prompt, "
                        f"{completion.usage.completion_tokens} na resposta, "
                        f"{total_cost} no total da conversa"
                    )
                break

            case "tool_calls":


                # O modelo pode solicitar várias tools em uma resposta.
                # Cada resultado é adicionado ao histórico antes da próxima chamada.

                # APPEND DA SOLICITAÇÃO DE TOOL NO HISTÓRICO

                if not message.tool_calls:
                    break

                requested_tool_calls = len(message.tool_calls)
                if tool_calls_count + requested_tool_calls > MAX_TOOL_CALLS:
                    print('Limite de chamadas de ferramentas atingido')
                    break

                historico_mensagens.append(message.model_dump(exclude_none=True))
                tool_calls_count += requested_tool_calls

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
                    except json.JSONDecodeError:
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

                    if not isinstance(arguments, dict):
                        historico_mensagens.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "name": function_name,
                            "content": f"Os argumentos da tool {function_name} devem ser um objeto JSON",
                        })

                        # Volta ao loop do agente

                        continue

                    try:
                        result = function(**arguments)
                    except (TypeError, ValueError) as error:
                        historico_mensagens.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "name": function_name,
                            "content": f"Erro ao executar a tool {function_name}: {error}",
                        })
                        continue

                    # EXECUÇÃO DA TOOL E APPEND DO RESULTADO NO HISTÓRICO

                    historico_mensagens.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": function_name,
                        "content": result,
                    })
            case "length":
                print("O agente atingiu o limite de tokens.")
                break
            case "content_filter":
                print("A resposta foi bloqueada pelo filtro de conteúdo.")
                break
            case _:
                print(f"Execução encerrada: {finish_reason}")
                break

    if not completed:
        # Não reutiliza uma solicitação que terminou no meio da geração.
        # Isso evita que o próximo turno herde tool calls/resultados incompletos.
        del historico_mensagens[turn_start_index:]

    if not completed and iterations >= MAX_ITERATIONS:
        print("Não consegui concluir dentro do limite de etapas.")
