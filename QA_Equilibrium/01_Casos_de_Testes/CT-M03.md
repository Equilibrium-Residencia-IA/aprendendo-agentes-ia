# CT-M03 — Atualização de fato pessoal estável

**Sistema sob teste:** A1 — Diário de Emoções (`04_diario_emocoes/`)  
**Tipo:** Teste funcional híbrido (Python + revisão humana)  
**Referência de código:** branch `main`, commit `d2782ac`  
**Execução:** EX01, 23/11/2026 às 21:35:44 (UTC−03:00)  
**Status global:** **APROVADO, COM PONTOS DE INVESTIGAÇÃO**

## Objetivo

Verificar se um fato pessoal estável, inicialmente armazenado, é substituído quando o usuário informa uma atualização e se o agente utiliza a informação vigente em uma nova *thread*, sem manter versões contraditórias como atuais.

## Escopo e pré-condições

O teste utiliza `fatos.json` temporário e independente dos dados pessoais do ambiente local. Os turnos 1 e 2 usam a mesma *thread*, enquanto o turno 3 usa uma nova *thread*, permitindo avaliar persistência fora do histórico conversacional da primeira. **Não valida reinício completo do processo Python.** O diário de eventos usa coleção temporária separada; a gravação eventual de um momento não constitui critério principal deste CT.

- Base de fatos inicialmente vazia: `{}`.
- Armazenamento do produto por `fatos.salvar_fato()` e leitura por `fatos.formatar_fatos()` no prompt dinâmico.
- Dados fictícios e ambiente de execução isolado.
- Versão de referência do agente: `openai/gpt-oss-120b`, temperatura `0.6`, conforme código examinado.

## Massa e procedimento

| Turno | Entrada enviada | Finalidade |
|---|---|---|
| 1 | `Sou professora em uma escola.` | Registrar profissão inicial |
| 2 | `Mudei de profissao. Agora sou coordenadora pedagogica.` | Atualizar a mesma profissão |
| 3 — nova *thread* | `Qual e minha profissao atual?` | Confirmar recuperação do fato vigente |

1. Validar fatos inicialmente vazios em diretório temporário.
2. Enviar os turnos 1 e 2 na mesma *thread*, capturando respostas e chamadas de ferramentas.
3. Inspecionar `fatos.json` após cada turno e verificar substituição da mesma chave.
4. Consultar a profissão atual em nova *thread* e verificar persistência.
5. Revisar o conteúdo conversacional e eventuais chamadas adicionais de ferramentas.

**Comando:** `python QA_Equilibrium/03_Automacao/testes_hibridos.py --ct M03`

## Registro da execução — EX01 híbrida

### Verificações automatizadas

| Critério | Resultado |
|---|---|
| `fatos_iniciais_vazios` | **PASS** |
| `fato_inicial_registrado` | **PASS** |
| `atualizacao_da_mesma_chave` | **PASS** |
| `profissao_anterior_nao_atual` | **PASS** |
| `profissao_atual_persistida` | **PASS** |
| `nenhum_fato_duplicado` | **PASS** |

**Status técnico:** `PASS` (6/6 verificações).

### Estados persistidos

| Momento | Conteúdo de fatos |
|---|---|
| Antes do teste | `{}` |
| Após turno 1 | `{"profissao": "professora em uma escola"}` |
| Após turno 2 | `{"profissao": "coordenadora pedagógica"}` |
| Após turno 3, nova *thread* | `{"profissao": "coordenadora pedagógica"}` |

A chave `profissao` foi reutilizada e o valor antigo deixou de representar a profissão atual. Não houve duplicação de chaves no arquivo de fatos.

### Comportamento do agente

| Turno | Resposta observada | Avaliação |
|---|---|---|
| 1 | “Entendo, você trabalha como professora em uma escola. Como foi o seu dia de trabalho hoje?” | Informação inicial reconhecida, sem extrapolação relevante |
| 2 | “Registro anotado. Como tem sido a adaptação à nova função de coordenadora pedagógica?” | Mudança reconhecida; uma pergunta contextual |
| 3 | “Sua profissão atual é coordenadora pedagógica.” | **Conforme:** informa a profissão vigente, sem confundi-la com a anterior |

**Consultou memória?** `false` nos três turnos, conforme JSON. Neste CT, isso **não caracteriza falha**: os fatos estáveis são injetados no prompt dinâmico via `formatar_fatos()`; não se exige chamada de `buscar_memoria`, ferramenta destinada aos momentos do diário.

### Análise das chamadas de ferramentas

No turno 2, o JSON enumera duas chamadas de `lembrar_fato`. A primeira possui **o mesmo ID** da chamada do turno 1 (`fc_c8bb090b-2228-4957-a986-3c5b71e72721`); a segunda possui ID próprio e atualiza `profissao` para `coordenadora pedagógica`. Como os dois turnos compartilharam uma *thread* e a coleta percorre `retorno['messages']` completo, a repetição é compatível com **recaptura de histórico**. O JSON isoladamente não sustenta alegação de gravação indevida do valor anterior durante o segundo turno.

Foram registradas duas chamadas distintas de `registrar_momento` no turno 2:

- Primeira tentativa: `ocorrido_em=2026-11-23T21:35:00`; ferramenta devolveu erro por considerar a data futura; **nenhum momento foi registrado nesta tentativa**.
- Segunda tentativa: `ocorrido_em=2026-11-23T21:30:00`; ferramenta devolveu “Momento registrado no diário.”

A alteração de profissão pode ser interpretada como acontecimento, mas o horário atribuído não consta da mensagem do usuário. O acionamento adicional e a definição de horário requerem análise específica; não alteram o resultado dos critérios de atualização de fatos deste CT.

### Revisão humana

| Critério | Avaliação |
|---|---|
| Profissão atual corretamente informada | **Conforme** |
| Profissão anterior não apresentada como vigente | **Conforme** |
| Ausência de detalhes pessoais inventados na resposta final | **Conforme** |
| Respostas proporcionais e sem diagnóstico | **Conforme** |
| Persistência acessível em nova *thread* | **Conforme** |
| Chamadas adicionais e instrumentação | Pontos de investigação; não houve impacto comprovado no fato persistido |

**Resultado EX01: APROVADO** — A atualização substituiu o valor anterior na mesma chave, permaneceu persistida e foi recuperada corretamente em nova *thread*. Não foram encontrados fatos pessoais contraditórios ou duplicados. Chamadas adicionais de ferramentas e recaptura de mensagens históricas permanecem como pontos de investigação, sem prejuízo comprovado ao objetivo deste CT.

## Achados e encaminhamentos

| ID | Evidência / observação | Encaminhamento |
|---|---|---|
| ACH-M03-001 | A coleta de ferramentas do turno 2 inclui chamada histórica de `lembrar_fato` do turno 1, com ID idêntico | Ajustar a instrumentação para registrar apenas mensagens novas de cada turno, evitando contagem duplicada de chamadas no relatório |
| ACH-M03-002 | Duas tentativas de `registrar_momento` no turno 2; primeira rejeitada como futura e segunda aceita | Investigar regras de atribuição de horário e o comportamento de correção após erro; avaliar se a gravação do evento está alinhada ao escopo |

Não foram identificados defeitos confirmados na substituição ou recuperação dos **fatos pessoais estáveis**.

## Evidências

| Identificador | Arquivo | Conteúdo |
|---|---|---|
| E01 | [CT-M03_EX01_E01_Resultado_Hibrido.png](../02_Evidencias/CT-M03/CT-M03_EX01_E01_Resultado_Hibrido.png) | Saída do terminal e seis verificações técnicas aprovadas |
| JSON | [CT-M03_20261123_213544_hibrido.json](../02_Evidencias/CT-M03/CT-M03_20261123_213544_hibrido.json) | Massa, respostas, parâmetros, IDs de chamadas e estados persistidos |

## Próximos passos

- Ajustar a captura incremental das chamadas de ferramentas em conversas com múltiplos turnos.
- Investigar as tentativas de gravação do momento e os horários atribuídos sem informação explícita.
- Executar regressão após alterações no produto ou na instrumentação, preservando esta execução como referência.
