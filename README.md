# Aprendendo a criar agentes de IA

Projeto de estudo: construir o mesmo tipo de agente (chat, tools, memória, RAG) em três níveis de abstração, para entender o que cada framework faz por baixo.

## Trilha

| Etapa | Pasta | O que você aprende |
|---|---|---|
| 1. Do zero | [01_do_zero/](01_do_zero/) | SDK da Groq (e OpenAI-compatível) puro: loop de chat, tool calling, validação, memória em JSON |
| 2. LangChain | [02_langchain/](02_langchain/) | Os mesmos conceitos com `ChatGroq`, `@tool` e `create_agent` |
| 3. LangGraph | [03_langgraph/](03_langgraph/) | Agente como grafo: estado, nós, arestas condicionais, checkpointer, store, embeddings e RAG |
| 4. Projeto final | [04_diario_emocoes/](04_diario_emocoes/) | Diário de Emoções: agente com tools, classificador de emoções, RAG sobre o próprio histórico e perfil vivo |
| Extra | [colab/](colab/) | Notebook do workshop |

### 01_do_zero
1. `01_chat.py` — chat simples com histórico
2. `02_tool_calling.py` — loop agêntico, tools com parâmetros, tratamento de erros
3. `03_tool_calling_memoria.py` — memória persistente (`memoria.json`)
4. `04_chat_neuralake.py` — mesmo chat usando outro provedor via SDK da OpenAI

### 02_langchain
1. `01_chat.py` — `ChatGroq` e classes de mensagem no lugar de dicts
2. `02_tool.py` — `@tool` e `create_agent` (o loop de tools vem pronto)
3. `03_memoria.py` — histórico entre turnos com checkpointer

### 03_langgraph
Cada arquivo evolui o anterior:
1. `01_fundacao.py` — grafo mínimo
2. `02_tool_horario.py` — tool + nó condicional
3. `03_historico.py` — histórico entre perguntas
4. `04_multiplas_escolhas.py` — nova tool
5. `05_memoria.py` — memória em JSON feita à mão
6. `06_memoria_langgraph.py` — checkpointer e store nativos
7. `07_embeddings.py` — embeddings e similaridade
8. `08_busca_semantica.py` — busca semântica no store
9. `09_documentos.py` — chunking e indexação
10. `10_rag_basico.py` — RAG completo (documentos em `docs/`)

### 04_diario_emocoes
Projeto final: o agente Conversador (A1) de um diário de emoções da Residência em IA. É um "ombro amigo" que registra momentos e consulta o histórico. Não é diagnóstico nem substitui um profissional.

1. `schema.py` — o que é uma entrada (`Entrada`), listas fechadas e o mapeamento GoEmotions → Plutchik
2. `classificador.py` — contrato da rede neural (`detectar_emocoes`); hoje usa um stub de palavras-chave
3. `armazenamento.py` — Chroma local com busca por similaridade e filtros de data e categoria
4. `tools.py` — `registrar_momento` (a RN classifica a emoção, não o LLM) e `buscar_memoria`
5. `agente.py` — `create_agent` com prompt dinâmico (data atual e perfil)
6. `main.py` — chat no terminal
7. `avaliacao.py` — `recuperacao` (sem LLM, calibra o limiar) e `comportamento` (conversas roteirizadas com o LLM)
8. `perfil.py` — perfil vivo reescrito a partir das entradas novas, com validação
9. `conhecimento.py` — RAG sobre fontes externas (PDFs em `RESOURCES_RAG/`): extração, chunking, coleção Chroma separada do diário e tool `consultar_conhecimento`

Os dados ficam em `04_diario_emocoes/state/` (Chroma e perfil), só no dispositivo e fora do git. O texto das conversas ainda vai para o LLM remoto.

```bash
python 04_diario_emocoes/conhecimento.py indexar         # (re)indexar os PDFs de RESOURCES_RAG
python 04_diario_emocoes/conhecimento.py buscar "estresse" # testar a recuperação
python 04_diario_emocoes/main.py                         # conversar
python 04_diario_emocoes/avaliacao.py recuperacao        # avaliar a busca
python 04_diario_emocoes/avaliacao.py comportamento      # avaliar o agente (chama o LLM)
```

## Como rodar

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

Crie um `.env` na raiz com as chaves (nomes variam por etapa):

```
GROQ_API_KEY=...        # quase todos os scripts
GROQ_AI_KEY=...         # só 01_do_zero/01_chat.py
NEURALAKE_API_KEY=...   # 01_do_zero/04
```

Execute os scripts a partir da raiz, por exemplo `python 03_langgraph/01_fundacao.py`.

> `memoria.json` é gerado em tempo de execução e está no `.gitignore`.
