# QA híbrido — Agente A1 / Diário de Emoções

## Escopo (CT-M01 a CT-M03)

Piloto de QA híbrido: verificações automáticas em Python, evidências JSON e avaliação humana documentada nos casos de teste. **O `PASS` técnico não representa aprovação global do CT.**

- **CT-M01:** registro de evento no diário, com verificação da base temporária e integridade do evento.
- **CT-M02:** recuperação de memória em nova thread, com busca-controle e verificação do retorno da ferramenta; não testa reinício do processo Python.
- **CT-M03:** atualização de fato pessoal estável em `fatos.json` temporário e consulta em nova thread.

Os relatórios, critérios e achados estão em `../01_Casos_de_Testes/`; a visão geral fica em `../QA_MESTRE.md`. Evidências e resultados são armazenados em `../02_Evidencias/`.

## Execução

Na **raiz do repositório `aprendendo-agentes-ia`**, com `.venv` configurado e `GROQ_API_KEY` carregada em `.env` local (arquivo não versionado):

```powershell
python QA_Equilibrium/03_Automacao/testes_hibridos.py --ct M01 --verificar
python QA_Equilibrium/03_Automacao/testes_hibridos.py --ct M01
python QA_Equilibrium/03_Automacao/testes_hibridos.py --ct M02
python QA_Equilibrium/03_Automacao/testes_hibridos.py --ct M03
```

Os testes usam a API Groq. A execução pode produzir respostas variáveis. A automação grava um novo JSON por execução em `QA_Equilibrium/02_Evidencias/<CT>/`; **não há aprovação final automática**.

## Cuidados e limitações

- Massa fictícia; não usar dados pessoais reais. Não versionar `.env`, tokens, `state/`, bases locais, logs privados ou documentos pessoais.
- CT-M02 usa memória semeada e nova thread; não comprova recuperação após reiniciar o processo.
- CT-M03 exige isolamento dos fatos: os registros de teste devem permanecer em diretório temporário.
- Revisões humanas são obrigatórias para adequação conversacional, fidelidade e conclusão global.
- O piloto documenta resultados observados nas execuções de 21–23/11/2026 (commit de referência `d2782ac`); não são resultados universais.

## Publicação

Este diretório foi preparado para uma **branch de contribuição de QA**, sem alterar o código do agente. Verificar o conteúdo dos prints e dos JSONs antes de tornar o repositório público ou abrir um PR.
