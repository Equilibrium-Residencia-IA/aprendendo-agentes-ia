# Guia de execução — Testes híbridos CT-M01 a CT-M03

**Projeto:** Equilibrium — Agente A1 (Diário de Emoções)  
**Situação:** piloto de QA híbrido, com execução automatizada e avaliação humana  
**Escopo:** comandos para reproduzir os testes CT-M01, CT-M02 e CT-M03

## 1. Pré-requisitos

- Repositório `aprendendo-agentes-ia` disponível localmente.
- Python e dependências instaladas conforme `requirements.txt` do projeto.
- Ambiente virtual `.venv` ativado.
- Variável `GROQ_API_KEY` configurada no `.env` local da raiz do repositório ou no ambiente. **Não versionar nem exibir essa chave.**
- Executar os comandos **na raiz de `aprendendo-agentes-ia`**, onde está a pasta `04_diario_emocoes`.

O script dos testes fica em `QA_Equilibrium/03_Automacao/testes_hibridos.py`, **dentro do repositório**.

## 2. Validar o ambiente

No terminal PowerShell do VS Code, com o repositório como diretório atual:

```powershell
python -m py_compile QA_Equilibrium/03_Automacao/testes_hibridos.py
python QA_Equilibrium/03_Automacao/testes_hibridos.py --ct M01 --verificar
```

- O primeiro comando verifica a sintaxe e retorna ao prompt sem mensagem quando não encontra erros.
- O segundo verifica a pasta do produto e a presença da chave; **não faz chamadas à Groq e não confirma que a chave funciona**.

## 3. Executar cada caso de teste

### CT-M01 — Registro de acontecimento

```powershell
python QA_Equilibrium/03_Automacao/testes_hibridos.py --ct M01
```

Verifica base temporária inicialmente vazia, chamada de `registrar_momento`, criação de um registro, preservação do relato original e interpretação da data relativa. **Revisar também** a resposta conversacional, a confirmação discreta do registro e a fidelidade do resumo.

### CT-M02 — Recuperação de memória

```powershell
python QA_Equilibrium/03_Automacao/testes_hibridos.py --ct M02
```

Prepara um evento fictício em base temporária, realiza busca-controle e verifica se o agente consulta e recupera a memória correta. **Limitação:** testa nova thread; não comprova recuperação após reiniciar o processo Python. Revisar a formulação da consulta, o retorno da ferramenta e a resposta final.

### CT-M03 — Atualização de fato pessoal estável

```powershell
python QA_Equilibrium/03_Automacao/testes_hibridos.py --ct M03
```

Testa registro inicial de profissão, atualização da mesma chave, substituição do valor anterior e recuperação do valor atualizado em nova thread. O teste utiliza **`fatos.json` temporário**, separado dos fatos reais. Revisar a resposta final e eventuais chamadas adicionais de ferramentas.

## 4. Localizar os resultados

Cada execução completa gera um **novo arquivo JSON** em:

```text
QA_Equilibrium/02_Evidencias/CT-M01/
QA_Equilibrium/02_Evidencias/CT-M02/
QA_Equilibrium/02_Evidencias/CT-M03/
```

O nome inclui data e horário da execução. O terminal apresenta os critérios técnicos, as ferramentas chamadas, as respostas e o caminho do JSON.

Os relatórios definitivos ficam em:

```text
QA_Equilibrium/01_Casos_de_Testes/CT-M01.md
QA_Equilibrium/01_Casos_de_Testes/CT-M02.md
QA_Equilibrium/01_Casos_de_Testes/CT-M03.md
QA_Equilibrium/QA_MESTRE.md
```

**Interpretação:** `PASS`/`FAIL` no terminal representa os **critérios automatizados**; a aprovação global do CT depende da análise humana registrada no respectivo Markdown. O JSON é evidência técnica; não substitui a conclusão do teste.

## 5. Cuidados de execução e publicação

- Não limpar nem alterar manualmente o ChromaDB original do projeto.
- Utilizar somente relatos fictícios; não publicar chaves, `.env`, dados pessoais, bancos locais ou arquivos de saúde.
- Não repetir testes apenas para obter um `PASS`: investigar resultados divergentes e preservar o histórico relevante.
- Conferir o conteúdo de JSONs e imagens antes de publicar a branch.
- A execução utiliza uma API de modelo de linguagem e, por isso, respostas e chamadas de ferramentas podem variar entre tentativas.

**Referências:** `QA_Equilibrium/03_Automacao/README.md` e os relatórios individuais dos CTs.
