import groq
import os
from dotenv import load_dotenv

from rich.console import Console
from rich.markdown import Markdown

load_dotenv()

console = Console()

api_key: str | None = os.getenv("GROQ_AI_KEY")

if api_key is None:
    print('API NÃO CONFIGURADA')

client: groq.Groq = groq.Groq(api_key=api_key)


historico_mensagens = []

while True:
    user_input: str = input('Input: ')
    if (user_input == ''):
        break
    historico_mensagens.append({
                    "role": "user",
                    "content": user_input
                })
    completion = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=historico_mensagens,
        temperature=0.6,
        max_completion_tokens=1024,
        top_p=0.8,
        reasoning_effort="medium",
    )
    ag_response: str = completion.choices[0].message.content or ""

    markdown = Markdown(ag_response)
    console.print(markdown)
    print('\n')
    if completion.usage is not None:
        print(
            f"Tokens: {completion.usage.prompt_tokens} usados no prompt, "
            f"{completion.usage.completion_tokens} na resposta, "
            f"{completion.usage.total_tokens} no total"
        )
    historico_mensagens.append({"role": "assistant", "content": ag_response})
