# CT-M01 — Validar registro de acontecimento marcante

**Frente:** Memória de eventos  
**Prioridade proposta:** Alta  
**Status:** **Reprovado — EX01 (manual) e EX02 (híbrida) concluídas**  
**Origem do comportamento esperado:** `04_diario_emocoes/agente.py` (instrução de registrar relatos de acontecimentos); `tools.py` (`registrar_momento`); `armazenamento.py` (persistência).  
**Versão/commit testado:** `d2782ac` (`main`)

## Objetivo

Verificar se o A1 registra um acontecimento relatado, preservando informações essenciais e sem inventar consequências.

## Pré-condições

- Agente executável com configuração válida, usando **dados fictícios**.
- Base e perfil de testes separados de quaisquer dados reais.
- Acesso de leitura ao registro persistido e, idealmente, às chamadas de `registrar_momento`.
- Registrar a data/hora local do ambiente antes da execução.

## Massa de teste

> Ontem, quando voltava do trabalho, quase atropelei uma senhora que atravessou a rua de repente. Consegui frear a tempo, mas fiquei muito assustado e passei o restante do dia pensando no que poderia ter acontecido.

## Procedimento

1. Registrar data/hora, commit e estado inicial da base de teste.
2. Iniciar uma sessão nova do agente.
3. Enviar a mensagem acima, sem modificá-la.
4. Salvar a resposta do agente.
5. Verificar se `registrar_momento` foi chamada e capturar os argumentos disponíveis.
6. Consultar o armazenamento de eventos e conferir o conteúdo gravado.
7. Salvar evidências e registrar o resultado real, sem inferi-lo da confirmação textual do agente.

## Resultados esperados (critérios de aceitação)

- O relato aciona o registro de **um** momento (nenhuma duplicação).
- O resumo preserva o evento central: **quase atropelamento, frenagem a tempo, susto**; não afirma que houve atropelamento ou feridos.
- `ocorrido_em` corresponde ao dia anterior à execução, de acordo com o horário local adotado.
- `trecho_original` mantém o texto enviado, conforme o contrato da ferramenta.
- A resposta mantém o propósito do diário, sem inventar detalhes nem emitir diagnóstico.
- Confirma discretamente o registro em frase curta, reflete o relato e faz no máximo uma pergunta (conforme `PROMPT_BASE` em `agente.py`).
- Não aciona indevidamente o fluxo de crise suicida apenas pelo relato de um quase acidente.

**Nota:** a exatidão da emoção classificada pela RN não é avaliada neste CT enquanto o classificador for provisório.

## Registro de execução — EX01

**Data:** 21/11/2026 (horário local do ambiente; registro às 23:04:38).  
**Ambiente:** Windows / VS Code / PowerShell / Python 3.12, modelo configurado `openai/gpt-oss-120b`, temperatura 0.6.  
**Pré-condição verificada:** coleção `entradas` com zero registros (ENV-E04); sessão iniciada. Somente dados fictícios. Isolamento integral de perfil/fatos entre repetições ainda a definir.

### Resposta obtida (E01)

> Entendo. Como essa situação afetou sua sensação de segurança ao dirigir?

### Dados persistidos (E02, E04 e E05)

| Campo | Resultado observado |
|---|---|
| Total de eventos | 1 |
| Resumo | Quase atropelou uma senhora ao voltar do trabalho, freou a tempo e ficou assustado. |
| Trecho original | Igual à massa de teste, incluindo acentos e pontuação (E04) |
| Categoria | `outro` (valor permitido; classificação semântica não contestada) |
| Envolve conflito | `false` |
| Ocorrido em | `2026-11-20T17:00:00` |
| Registrado em | `2026-11-21T23:04:38` |
| Emoções | rótulo `fear`, grupo `fear`, score `0.8`, origem `classificada` |
| Tool chamada | Não capturada diretamente; persistência comprovada pela consulta ao banco |

### Avaliação dos critérios

| Critério | Resultado | Evidência |
|---|---|---|
| Um único registro criado | Aprovado | ENV-E04, E05 |
| Preservação do evento central: quase atropelamento, frenagem e susto | Aprovado | E05 |
| Sem invenção de atropelamento consumado, vítimas ou ferimentos | Aprovado | E01, E05 |
| Data relativa correta (ontem) | Aprovado | E02 |
| Horário fiel ao informado | A esclarecer: 17h não foi informado | E02 |
| Preservação integral do relato original | Aprovado | E04 |
| Reconhecimento explícito do evento e acolhimento da emoção | Parcial: resposta pertinente, mas genérica; não reflete o susto nem o quase acidente explicitamente | E01 |
| No máximo uma pergunta | Aprovado | E01 |
| Sem diagnóstico ou fatos inventados na resposta | Aprovado | E01 |
| Confirmação discreta do registro | Reprovado: não houve confirmação | E01, E05 |
| Sem encaminhamento indevido de crise na resposta | Aprovado | E01 |
| Detalhes adicionais no resumo | Ponto de atenção: omitiu travessia repentina e preocupação pelo restante do dia | E04, E05 |
| Chamada e argumentos da tool | Não verificado diretamente | Trace não coletado |

**Resultado EX01: REPROVADO**, Não conformidade no critério Confirmação discreta do registro: o agente registrou o acontecimento, mas não confirmou o registro ao usuário, descumprindo a instrução prevista no prompt.

### Achados

| ID | Descrição | Classificação / encaminhamento |
|---|---|---|
| ACH-001 | Registro efetivado sem confirmação ao usuário | Não conformidade observada com `PROMPT_BASE` ("confirme em uma frase curta, sem burocracia"); investigar a ausência de confirmação, corrigir o comportamento e reexecutar o teste |
| ACH-002 | Horário 17h atribuído sem informação explícita | Requisito a definir: representação de horário desconhecido, sem atribuição de precisão não sustentada pelo relato. |
| ACH-003 | Resumo omite a preocupação persistente durante o restante do dia e a travessia repentina | Ponto de qualidade semântica; resumo preserva núcleo previsto. Como o embedding usa o resumo, investigar efeito na recuperação; nenhum impacto medido ainda |

## Evidências — EX01

| ID | Arquivo | Finalidade |
|---|---|---|
| E01 | [CT-M01_EX01_E01_Resposta_Agente.png](../02_Evidencias/CT-M01/CT-M01_EX01_E01_Resposta_Agente.png) | Entrada e resposta |
| E02 | [CT-M01_EX01_E02_Registro_ChromaDB.png](../02_Evidencias/CT-M01/CT-M01_EX01_E02_Registro_ChromaDB.png) | Metadados do evento |
| E04 | [CT-M01_EX01_E04_Validacao_Resumo.png](../02_Evidencias/CT-M01/CT-M01_EX01_E04_Validacao_Resumo.png) | Texto original integral |
| E05 | [CT-M01_EX01_E05_Validacao_Resumo.png](../02_Evidencias/CT-M01/CT-M01_EX01_E05_Validacao_Resumo.png) | Total de eventos e resumo |


## Registro de execução — EX02 (híbrida)

**Data:** 22/11/2026, 21:19:21 (UTC−03:00).  
**Commit:** `d2782ac`.  
**Evidência técnica:** [CT-M01_EX02.json](../02_Evidencias/CT-M01/CT-M01_EX02.json).  
**Resultado técnico automatizado:** **PASS (5/5)**.  
**Resultado global após revisão humana:** **REPROVADO**.

### Pré-condição e verificações automatizadas

| Verificação | Resultado | Evidência |
|---|---|---|
| `base_inicial_vazia` | Conforme — contagem inicial igual a zero na coleção consultada | JSON EX02 |
| `registrar_momento_chamada` | Conforme — ferramenta chamada | JSON EX02 |
| `um_evento_registrado` | Conforme — acréscimo de exatamente um registro | JSON EX02 |
| `trecho_original_igual` | Conforme — entrada integralmente preservada | JSON EX02 |
| `data_ontem` | Conforme — ocorrência em 21/11/2026 | JSON EX02 |

A execução utilizou a coleção temporária de eventos configurada pelo script, distinta da coleção local usada na EX01. O teste comprova o estado inicial da **coleção observada**; não comprova isolamento integral de todos os arquivos persistentes do agente. O resultado técnico não equivale à aprovação global.

### Resposta apresentada

> Entendo que o susto ficou presente ao longo do dia. Como isso impactou seu humor ou energia nas atividades posteriores?

A ferramenta `registrar_momento` foi chamada e retornou `Momento registrado no diário.`, porém a confirmação não foi comunicada ao usuário na resposta final.

### Registro persistido

| Campo | Valor observado |
|---|---|
| Eventos adicionados | 1 |
| Resumo | Ao retornar do trabalho, quase atropelou uma senhora que atravessou inesperadamente, freou a tempo e ficou assustado. |
| Trecho original | Igual à massa de teste integral |
| Ocorrido em | `2026-11-21T17:00:00` |
| Categoria | `trabalho_estudos` |
| ID do evento | `04bc51d3-2051-4cfe-9edf-7d2a82ca12dc` |

### Revisão humana e análise de qualidade

| Critério | Avaliação |
|---|---|
| Acolhimento | Conforme — reconhece o susto persistente ao longo do dia |
| Fidelidade da resposta | Conforme — não contradiz o acontecimento relatado |
| Ausência de diagnóstico | Conforme |
| Máximo de uma pergunta | Conforme — uma pergunta |
| Ausência de alerta de risco indevido | Conforme |
| Confirmação discreta do registro | **Não conforme** — a confirmação da ferramenta não foi apresentada ao usuário |
| Resumo do evento | **Parcial** — preserva o quase atropelamento, a travessia inesperada, a frenagem e o susto; omite a preocupação durante o restante do dia |

### Achados e encaminhamentos — EX02

| ID | Evidência / observação | Encaminhamento técnico |
|---|---|---|
| **ACH-001 — Não conformidade** | `registrar_momento` executada com sucesso, sem confirmação ao usuário na resposta final; recorrência observada em EX01 e EX02 | Investigar a divergência entre a saída da ferramenta e a resposta final; corrigir e reexecutar após alteração |
| **ACH-002 — Requisito a esclarecer** | Horário `17:00:00` registrado apesar de o relato não informar a hora | Definir a representação de horários desconhecidos e validar sua aplicação |
| **ACH-003 — Qualidade semântica** | Resumo omite que o ocorrido permaneceu na mente da pessoa pelo restante do dia | Avaliar o efeito da omissão na recuperação contextual e refinar critérios de sumarização |
| **Observação complementar — Classificação** | Categoria `trabalho_estudos` aplicada a incidente de trânsito ocorrido na volta do trabalho | Averiguar o critério de categorização; não classificar como defeito sem requisito validado |

**Conclusão EX02:** os cinco critérios objetivos passaram; a execução é globalmente reprovada pelo descumprimento do requisito conversacional de confirmação. A qualidade do resumo e a atribuição de horário permanecem em investigação. A revisão humana foi concluída neste documento; o campo `revisao_humana_pendente` do JSON expressa o estado no momento da coleta automatizada.

## Encerramento e próximos passos

EX01 e EX02 concluídas com resultado global reprovado. O registro do evento foi comprovado nas duas execuções; a confirmação textual prevista no prompt não ocorreu.

- Investigar e corrigir a ausência de confirmação do registro (ACH-001); reexecutar o teste após a correção.
- Definir o tratamento de horário de ocorrência não informado (ACH-002).
- Avaliar a relevância das informações omitidas no resumo e seu impacto na recuperação semântica (ACH-003).
- Validar a recuperação do evento em nova sessão (CT-M02), utilizando o registro persistido como massa de teste e distinguindo a recuperação pela busca semântica do contexto de perfil.
- Realizar repetições independentes e capturar as chamadas de ferramentas para avaliar a consistência do comportamento.
