# CT-M04 — Resposta a relato cotidiano

**Sistema sob teste:** A1 — Diário de Emoções (`04_diario_emocoes/`)  
**Frente:** Comportamento conversacional e registro de momentos  
**Tipo:** Teste funcional híbrido (Python + revisão humana)  
**Referência de código do produto:** commit `98ff24b`  
**Execução:** EX01, 25/11/2026 às 13:22:21 (UTC−03:00)  
**Status global:** **REPROVADO**

## Objetivo

Verificar se o agente responde de maneira adequada a um relato cotidiano, reconhece o acontecimento e o sentimento explicitamente declarado, registra o momento com integridade e respeita as instruções conversacionais vigentes, incluindo a confirmação discreta do registro.

## Escopo e pré-condições

- Execução em `aprendendo-agentes-ia`, com ambiente virtual Python e configuração de API disponíveis.
- Coleção temporária do ChromaDB destinada exclusivamente ao teste, inicialmente vazia (`base_inicial_vazia=true`).
- Massa fictícia, sem alteração intencional na coleção real de eventos.
- Avaliação limitada ao registro do relato e ao comportamento conversacional nessa interação; não inclui recuperação em nova *thread* nem avaliação da rede neural de emoções.
- Critérios interpretados segundo o prompt em vigor no commit avaliado; eventual mudança futura no requisito de confirmação deverá ser avaliada em nova versão.

## Massa de teste

> Hoje, depois do almoco, fiz uma caminhada de meia hora no parque. Foi agradavel e me senti tranquilo.

O texto foi mantido exatamente como enviado pelo script, inclusive a grafia sem acentos.

## Procedimento

1. Preparar uma coleção de eventos temporária e confirmar que possui zero registros.
2. Enviar a massa fictícia ao agente e capturar a resposta e as chamadas de ferramentas com seus argumentos e resultados.
3. Verificar o número de eventos gravados, a preservação do texto original e a data de ocorrência.
4. Avaliar manualmente acolhimento, fidelidade à entrada, limite de perguntas, ausência de diagnóstico e alerta indevido, confirmação do registro e coerência do resumo/categoria.
5. Registrar os achados, distinguindo critérios não conformes de pontos ainda sujeitos a investigação.

**Comando executado na raiz do repositório:**

```powershell
python QA_Equilibrium/03_Automacao/testes_hibridos.py --ct M04
```

## Registro de execução — EX01

**Data/hora:** `2026-11-25T13:22:21-03:00`  
**Commit do produto informado no JSON:** `98ff24b`  
**Resultado técnico:** **PASS (5/5)**  
**Resultado global após revisão humana:** **REPROVADO**

### Verificações automatizadas

| Critério | Resultado |
|---|---|
| `base_inicial_vazia` | **PASS** |
| `registrar_momento_chamada` | **PASS** |
| `um_evento_persistido` | **PASS** |
| `trecho_original_preservado` | **PASS** |
| `data_hoje` | **PASS** |

A coleção passou de **0 para 1 evento**. O resultado `PASS` dessas verificações não constitui aprovação global do CT.

**Consultou memória?** `false`. Não era requisito deste cenário: o agente deveria registrar um relato atual, e não recuperar evento anterior.

### Resultado conversacional

**Resposta observada:**

> Entendo, você caminhou meia hora no parque após o almoço e sentiu tranquilidade. Como foi seu dia de trabalho hoje?

| Critério | Avaliação | Fundamentação |
|---|---|---|
| Reconhecimento do acontecimento | **Conforme** | Retoma caminhada de meia hora, parque e período após o almoço. |
| Reconhecimento do sentimento informado | **Conforme** | Reconhece tranquilidade sem acrescentar emoções não relatadas. |
| Tom profissional e acolhedor | **Conforme** | Resposta concisa e cordial. |
| No máximo uma pergunta | **Conforme** | Há uma pergunta na resposta final. |
| Ausência de diagnóstico ou detalhes inventados | **Conforme** | Não atribui condição clínica ou fatos pessoais não fornecidos. |
| Confirmação discreta do registro | **Não conforme** | O registro foi efetuado, mas a resposta ao usuário não confirma que foi realizado. |
| Ausência de alerta de crise indevido | **Conforme** | Nenhum alerta de crise foi apresentado. |
| Mudança de tema para trabalho | **Observação** | A pergunta sobre o trabalho não decorre diretamente da caminhada, mas é compatível com o prompt que orienta explorar diferentes temas; não foi classificada como não conformidade. |

### Registro persistido

| Campo | Valor observado |
|---|---|
| Quantidade de eventos ao final | **1** |
| Resumo | Caminhou meia hora no parque e sentiu tranquilidade. |
| Categoria | `corpo_saude` |
| Data/hora de ocorrência | `2026-11-25T13:00:00` |
| Texto original | Preservado integralmente; igual à massa de teste |

O resumo contempla a caminhada, sua duração e a tranquilidade relatada; a categoria `corpo_saude` é compatível com a atividade física descrita. A ausência de referência ao almoço/parque no resumo não comprometeu as informações centrais observadas, mas pode ser considerada em avaliações futuras de recuperação.

### Análise das chamadas de ferramenta e recuperação após erro

Foram **duas chamadas distintas** de `registrar_momento`, com identificadores diferentes:

| Tentativa | Horário enviado em `ocorrido_em` | Retorno da ferramenta | Efeito observado |
|---|---|---|---|
| 1 | `2026-11-25T13:30:00` | Erro: horário futuro; nada registrado | Registro rejeitado |
| 2 | `2026-11-25T13:00:00` | `Momento registrado no diário.` | Registro efetuado |

A segunda chamada demonstra **recuperação operacional após o erro da ferramenta**, coerente com a orientação do prompt para corrigir argumentos e tentar novamente. O sistema terminou com apenas um evento persistido, sem duplicação observada.

O horário informado pelo usuário foi somente **“depois do almoço”**; nem 13h30 nem 13h00 foram especificados. Portanto, a atribuição de um horário exato continua como ponto de investigação. A recuperação após erro é um resultado positivo, mas não valida automaticamente a precisão do horário final.

## Avaliação dos critérios e achados

| Identificador | Observação fundamentada | Classificação / encaminhamento |
|---|---|---|
| **ACH-001 (recorrente)** | O agente persistiu o momento, porém não confirmou esse registro na resposta conversacional. | **Não conformidade** frente ao prompt vigente. Reavaliar em nova versão caso a instrução seja modificada. |
| **ACH-M04-001** | Duas tentativas de registro: primeira rejeitada por horário futuro, segunda bem-sucedida; horário final não informado pelo usuário. | **Ponto de investigação:** definir regra para horário não especificado e preservar a correção de erros de ferramenta sem introduzir precisão indevida. |

Não foi observada duplicação de evento. A correção do argumento após falha da ferramenta constitui **comportamento positivo** na presente execução.

## Evidências

| ID | Arquivo | Conteúdo |
|---|---|---|
| E01 | [CT-M04_EX01_E01_Resultado_Hibrido.png](../02_Evidencias/CT-M04/CT-M04_EX01_E01_Resultado_Hibrido.png) | Resultado do terminal, cinco verificações técnicas e resposta do agente |
| JSON | [CT-M04_20261125_132221_hibrido.json](../02_Evidencias/CT-M04/CT-M04_20261125_132221_hibrido.json) | Entrada, chamadas/argumentos/saídas das ferramentas, registro persistido, estado da coleção e metadados da execução |

## Conclusão

**Resultado EX01: REPROVADO** — Não conformidade no critério *Confirmação discreta do registro*: o acontecimento foi registrado corretamente, mas o agente não comunicou o registro ao usuário, em desacordo com a instrução vigente no prompt.

## Próximos passos

- Reavaliar o critério de confirmação após alteração efetiva e versionada do prompt, caso aprovada.
- Investigar a atribuição de horários exatos quando o usuário informa apenas uma referência aproximada.
- Preservar e avaliar em regressão o comportamento de recuperação após rejeição de argumentos pela ferramenta.
