
# IMPORTS
# datetime fornece o horário atual e também registra quando uma memória foi criada.

from datetime import datetime
# json é usado tanto para interpretar os argumentos das tools quanto para ler/escrever
# o arquivo persistente de memórias.
import json
# Path permite montar o caminho do arquivo memoria.json de forma independente do sistema.
from pathlib import Path
# groq é o SDK usado para conversar com o modelo hospedado na Groq.
import groq
# os permite ler a chave da API a partir das variáveis de ambiente.
import os
# load_dotenv carrega variáveis definidas em um arquivo .env local.
from dotenv import load_dotenv
# Esse tipo descreve o formato esperado pela lista de tools enviada à API.
from groq.types.chat import ChatCompletionToolParam

# Console e Markdown deixam a resposta do modelo mais legível no terminal.
from rich.console import Console
from rich.markdown import Markdown

# CARREGAR AMBIENTE

# Procura um arquivo .env e disponibiliza suas variáveis via os.getenv.
load_dotenv()

# Console é reutilizado para imprimir as respostas formatadas.
console = Console()

# A chave não fica escrita no código; ela deve existir no ambiente ou no .env.
api_key: str | None = os.getenv("GROQ_API_KEY")

# Sem a chave, não faz sentido iniciar o agente: falhamos explicitamente.
if api_key is None:
    raise RuntimeError("A variável de ambiente GROQ_API_KEY não está configurada.")

# O cliente encapsula as chamadas HTTP para a API da Groq.
client: groq.Groq = groq.Groq(api_key=api_key)

# A memória fica ao lado deste script, em 01_do_zero/memoria.json.
# Assim, ela continua disponível quando o programa for encerrado e aberto novamente.
MEMORY_FILE = Path(__file__).with_name("memoria.json")
# Evita enviar uma quantidade ilimitada de memórias ao modelo em uma única pergunta.
MAX_RETRIEVED_MEMORIES = 5


def normalize_words(text: str) -> set[str]:
    """Converte um texto em palavras comparáveis para a busca simples."""
    # Pontuação nas extremidades não deve impedir uma correspondência.
    # Palavras com até dois caracteres são ignoradas para reduzir coincidências genéricas.
    return {
        word.strip(".,!?;:").casefold()
        for word in text.split()
        if len(word.strip(".,!?;:")) > 2
    }


def load_memories() -> list[dict[str, str]]:
    """Carrega e valida a lista de memórias armazenada no JSON."""
    # Na primeira execução o arquivo ainda não existe; isso representa memória vazia.
    if not MEMORY_FILE.exists():
        return []

    try:
        # O JSON esperado é uma lista de objetos como:
        # {"content": "Prefere respostas curtas", "created_at": "..."}.
        with MEMORY_FILE.open(encoding="utf-8") as file:
            memories = json.load(file)
    except json.JSONDecodeError as error:
        # Não escondemos corrupção do arquivo: o erro precisa ser corrigido explicitamente.
        raise RuntimeError(f"O arquivo de memória está inválido: {MEMORY_FILE}") from error

    # A validação evita que dados inesperados provoquem erros mais adiante.
    if not isinstance(memories, list) or not all(
        isinstance(memory, dict)
        and isinstance(memory.get("content"), str)
        and isinstance(memory.get("created_at"), str)
        for memory in memories
    ):
        raise RuntimeError(f"O formato do arquivo de memória é inválido: {MEMORY_FILE}")

    return memories


def save_memory(content: str) -> str:
    """Adiciona uma memória ao JSON, evitando duplicatas exatas."""
    # Remove espaços acidentais antes de salvar.
    normalized_content = content.strip()
    if not normalized_content:
        # Uma memória vazia não teria valor para recuperação futura.
        raise ValueError("A memória não pode estar vazia.")

    # Sempre lemos o arquivo antes de escrever para preservar memórias anteriores.
    memories = load_memories()
    # casefold permite comparar textos sem diferenciar maiúsculas de minúsculas.
    if any(memory["content"].casefold() == normalized_content.casefold() for memory in memories):
        return "Essa memória já está salva."

    # A data ajuda a desempatar resultados e permite saber quando a memória foi criada.
    memories.append({
        "content": normalized_content,
        "created_at": datetime.now().isoformat(timespec="seconds"),
    })
    # ensure_ascii=False preserva acentos; indent=2 mantém o arquivo legível.
    with MEMORY_FILE.open("w", encoding="utf-8") as file:
        json.dump(memories, file, ensure_ascii=False, indent=2)

    return "Memória salva com sucesso."


def retrieve_memories(query: str) -> list[str]:
    """Retorna as memórias que compartilham mais palavras com a consulta."""
    query_words = normalize_words(query)
    if not query_words:
        # Sem palavras úteis, não há como fazer uma busca relevante.
        return []

    # Cada item terá: pontuação, data de criação e conteúdo.
    scored_memories = []
    for memory in load_memories():
        memory_words = normalize_words(memory["content"])
        # A interseção mede quantas palavras da consulta aparecem na memória.
        score = len(query_words & memory_words)
        if score:
            scored_memories.append((score, memory["created_at"], memory["content"]))

    # Memórias com mais coincidências vêm primeiro; em empate, as mais recentes.
    scored_memories.sort(key=lambda item: (item[0], item[1]), reverse=True)
    # Retornamos somente o texto, limitado para controlar o tamanho do contexto.
    return [
        content
        for _, _, content in scored_memories[:MAX_RETRIEVED_MEMORIES]
    ]


# DEFINIÇÃO DAS TOOLS DISPONÍVEIS:
# Uma tool tem duas partes:
# 1. o schema abaixo, que explica ao modelo quando e como chamá-la;
# 2. uma função Python no mapa tool_functions, executada quando a API solicitar.

tools: list[ChatCompletionToolParam] = [
    {
        # A API identifica esta entrada como uma função executável.
        "type": "function",
        "function": {
            # O nome precisa ser exatamente igual ao nome no mapa de funções.
            "name": "getTimeNow",

            # A descrição orienta o modelo sobre a finalidade da tool.
            "description": "Retrieves the current time at the user location",

            # Esta tool não recebe argumentos.
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "askWithMultipleChoice",
            "description": "Ask a question, with some choices to the user to choose, the user can also write his own answer",
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
            # strict exige que os argumentos respeitem o schema declarado.
            "strict": True,
        },
    },
    {
        # Essa tool é a única forma de captura nesta primeira versão:
        # o modelo precisa decidir explicitamente chamá-la.
        "type": "function",
        "function": {
            "name": "saveMemory",
            "description": "Saves an important user preference or fact for future conversations.",
            "parameters": {
                "type": "object",
                "properties": {
                    "content": {
                        "type": "string",
                        "description": "The preference or fact to remember",
                    },
                },
                "required": ["content"],
                "additionalProperties": False,
            },
            "strict": True,
        },
    },
    {
        # Essa tool permite uma busca manual durante a conversa.
        # Além disso, o programa faz uma busca automática antes de cada pergunta.
        "type": "function",
        "function": {
            "name": "retrieveMemory",
            "description": "Retrieves saved memories relevant to a user question.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The topic to search for in saved memories",
                    },
                },
                "required": ["query"],
                "additionalProperties": False,
            },
            "strict": True,
        },
    }
]


def getTimeNow() -> str:
    """Retorna o horário local no formato HH:MM."""
    time_now = datetime.now()
    return time_now.strftime("%H:%M")


def askWithMultipleChoice(question: str, choices: list[str]) -> str:
    """Mostra opções no terminal e devolve a escolha do usuário ao modelo."""
    print(f"Pergunta: {question}")
    print("---------------------")
    print("Selecione a resposta:")
    for i, choice in enumerate(choices):
        print(f"{i}) {choice}")
    print("---------------------")

    answer = input("> ")

    try:
        # O usuário pode informar o índice numérico de uma opção.
        choice_index = int(answer)
    except ValueError:
        # Se ele escrever texto, preservamos a resposta livre.
        return (
            f"Pergunta recebida pelo usuário: {question}; "
            f"Resposta do usuário: {answer}"
        )

    if 0 <= choice_index < len(choices):
        # Índice válido: devolvemos o texto da opção escolhida, não apenas o número.
        return (
            f"Pergunta recebida pelo usuário: {question}; "
            f"Resposta do usuário: {choices[choice_index]}"
        )

    # Índice inválido: também preservamos o valor digitado para o modelo interpretar.
    return (
        f"Pergunta recebida pelo usuário: {question}; "
        f"Resposta do usuário: {answer}"
    )

def saveMemory(content: str) -> str:
    """Adaptador da função interna para o nome exposto como tool ao modelo."""
    return save_memory(content)


def retrieveMemory(query: str) -> str:
    """Adaptador que transforma a lista de resultados em texto para a API."""
    memories = retrieve_memories(query)
    if not memories:
        return "Nenhuma memória relevante foi encontrada."
    return "\n".join(f"- {memory}" for memory in memories)


# MAPA ENTRE O NOME DA TOOL E A FUNÇÃO PYTHON QUE SERÁ EXECUTADA
# Quando o modelo pede, por exemplo, "saveMemory", este dicionário encontra
# a função Python que deve ser chamada.

tool_functions = {
    "getTimeNow": getTimeNow,
    "askWithMultipleChoice": askWithMultipleChoice,
    "saveMemory": saveMemory,
    "retrieveMemory": retrieveMemory,
}

# INICIANDO O AGENTE

# Mensagem visual para indicar que o programa iniciou.
print('''
==========================
        R・IA AGENT
==========================
''')

# Este histórico é a memória de contexto da sessão atual.
# Ele é diferente de memoria.json: desaparece quando o processo termina.
historico_mensagens = []
# Evita que uma pergunta fique presa em um ciclo infinito de chamadas.
MAX_ITERATIONS = 6
# Protege contra uma resposta do modelo solicitando tools demais.
MAX_TOOL_CALLS = 10
# Limita o tamanho máximo de cada resposta gerada pelo modelo.
MAX_COMPLETION_TOKENS = 32000

# LOOP AGENTICO

# Cada passagem por este loop representa uma nova pergunta do usuário.
while True:
    # INTERAÇÃO COM O USUÁRIO

    user_input: str = input('Input: ')

    # Uma entrada vazia é o comando para encerrar o programa.
    if user_input.strip() == '':
        print('Saindo da interação com o RIA')
        break

    # Guardamos o início do turno para conseguir removê-lo se a execução falhar.
    turn_start_index = len(historico_mensagens)
    # A busca automática injeta no contexto somente memórias relacionadas à pergunta.
    relevant_memories = retrieve_memories(user_input)
    if relevant_memories:
        # A mensagem system orienta o modelo, mas não é uma nova fala do usuário.
        historico_mensagens.append({
            "role": "system",
            "content": (
                "Memórias relevantes de conversas anteriores. "
                "Use-as apenas quando forem úteis e não as invente:\n"
                + "\n".join(f"- {memory}" for memory in relevant_memories)
            ),
        })
    # A pergunta entra depois das memórias, para o modelo usá-las como contexto.
    historico_mensagens.append({
        "role": "user",
        "content": user_input,
    })

    # CHAMADA À API

    # Esses contadores são reiniciados para cada pergunta.
    iterations = 0
    tool_calls_count = 0
    completed = False
    total_cost = 0

    # Uma iteração pode ser: chamada do modelo -> tool -> nova chamada do modelo.
    while iterations < MAX_ITERATIONS:
        iterations += 1
        
        completion = client.chat.completions.create(

            # O modelo recebe todo o contexto acumulado da sessão.
            # As tools e a memória persistente complementam esse histórico.

            messages=historico_mensagens,

            # CONFIGS DO MODELO:

            # Modelo usado para responder e decidir quando chamar tools.
            model="openai/gpt-oss-120b",
            # Controla o esforço de raciocínio disponibilizado pelo modelo.
            reasoning_effort="medium",
            # Valores maiores deixam a resposta mais variável.
            temperature=0.6,
            # Limite de tokens gerados nesta chamada.
            max_completion_tokens=MAX_COMPLETION_TOKENS,
            # Controla a diversidade de tokens considerados.
            top_p=0.8,

            # TOOLS:

            # O modelo pode escolher automaticamente entre responder e usar uma tool.
            tools=tools,
            tool_choice="auto",
        )

        # A primeira escolha contém a mensagem produzida pelo modelo.
        message = completion.choices[0].message
        # finish_reason informa se houve resposta normal ou solicitação de tool.
        finish_reason = completion.choices[0].finish_reason

        # RETORNO DA TOOL

        match finish_reason:
            case "stop":

                # RETORNO E FORMATAÇÃO
                # stop significa que o modelo terminou uma resposta final.
                completed = True

                # content pode ser None; nesse caso usamos texto vazio para manter str.
                ag_response: str = message.content or ""
                historico_mensagens.append({
                    "role": "assistant",
                    "content": ag_response,
                })

                # Markdown interpreta formatação como listas, negrito e código.
                console.print(Markdown(ag_response))
                print('\n')

                # PRINT DO TOKEN_USAGE

                if completion.usage is not None:
                    # total_cost é, neste código, uma contagem acumulada de tokens,
                    # não um valor monetário apesar do nome da variável.
                    total_cost += completion.usage.total_tokens
                    print(
                        f"Tokens: {completion.usage.prompt_tokens} usados no prompt, "
                        f"{completion.usage.completion_tokens} na resposta, "
                        f"{total_cost} no total da conversa"
                    )
                    if total_cost > 8000:
                        # Remove mensagens antigas para reduzir o próximo contexto.
                        # O histórico persistente em memoria.json não é apagado aqui.
                        historico_mensagens.pop(0)
                        historico_mensagens.pop(1)
                break

            case "tool_calls":

                # O modelo pode solicitar várias tools em uma resposta.
                # Cada resultado é adicionado ao histórico antes da próxima chamada.

                # APPEND DA SOLICITAÇÃO DE TOOL NO HISTÓRICO

                if not message.tool_calls:
                    # Proteção contra uma resposta inconsistente da API.
                    break

                requested_tool_calls = len(message.tool_calls)
                if tool_calls_count + requested_tool_calls > MAX_TOOL_CALLS:
                    # Interrompe antes de executar além do limite definido.
                    print('Limite de chamadas de ferramentas atingido')
                    break

                # A própria solicitação precisa entrar no histórico para que a API
                # consiga relacioná-la aos resultados role=tool seguintes.
                historico_mensagens.append(message.model_dump(exclude_none=True))
                tool_calls_count += requested_tool_calls

                for tool_call in message.tool_calls:

                    # IDENTIFICAÇÃO DA TOOL SOLICITADA

                    # O nome vem do modelo e é usado para consultar o mapa local.
                    function_name = tool_call.function.name
                    function = tool_functions.get(function_name)

                    if function is None:
                        # Em vez de quebrar o agente, devolvemos o erro ao próprio modelo.
                        historico_mensagens.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "name": function_name,
                            "content": f"Tool desconhecida: {function_name}",
                        })

                        # O modelo terá outra oportunidade de corrigir a chamada.
                        continue

                    # LEITURA E VALIDAÇÃO DOS ARGUMENTOS DA TOOL

                    try:
                        # A API envia os argumentos como uma string JSON.
                        arguments = json.loads(tool_call.function.arguments or "{}")
                    except json.JSONDecodeError:
                        # O erro vira uma mensagem de tool para o modelo entender.
                        historico_mensagens.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "name": function_name,
                            "content": f"Argumentos inválidos para a tool {function_name}",
                        })

                        continue

                    if not isinstance(arguments, dict):
                        # O operador **arguments abaixo exige um objeto/dicionário.
                        historico_mensagens.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "name": function_name,
                            "content": f"Os argumentos da tool {function_name} devem ser um objeto JSON",
                        })

                        continue

                    try:
                        # Desempacota o JSON como argumentos da função Python.
                        result = function(**arguments)
                    except (TypeError, ValueError) as error:
                        # TypeError cobre argumentos incompatíveis; ValueError cobre
                        # valores rejeitados pela própria função, como memória vazia.
                        historico_mensagens.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "name": function_name,
                            "content": f"Erro ao executar a tool {function_name}: {error}",
                        })
                        continue

                    # EXECUÇÃO DA TOOL E APPEND DO RESULTADO NO HISTÓRICO

                    # O resultado precisa referenciar o mesmo tool_call_id da solicitação.
                    # Assim a API sabe qual resposta pertence a qual chamada.
                    historico_mensagens.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": function_name,
                        "content": result,
                    })
            case "length":
                # O modelo tentou gerar mais tokens do que o limite permitido.
                print("O agente atingiu o limite de tokens.")
                break
            case "content_filter":
                # A resposta foi bloqueada pelas políticas do provedor.
                print("A resposta foi bloqueada pelo filtro de conteúdo.")
                break
            case _:
                # Tratamento explícito para outros motivos retornados pela API.
                print(f"Execução encerrada: {finish_reason}")
                break

    if not completed:
        # Não reutiliza uma solicitação que terminou no meio da geração.
        # Isso evita que o próximo turno herde tool calls/resultados incompletos.
        # Também remove as memórias system injetadas no início deste turno.
        del historico_mensagens[turn_start_index:]

    if not completed and iterations >= MAX_ITERATIONS:
        # Informa ao usuário que o limite de tentativas foi atingido.
        print("Não consegui concluir dentro do limite de etapas.")
