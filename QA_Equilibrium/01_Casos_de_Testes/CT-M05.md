# CT-M05 — Dois acontecimentos em uma única mensagem

**Sistema sob teste:** A1 — Diário de Emoções (`04_diario_emocoes/`)  
**Frente:** Separação de acontecimentos e comportamento conversacional  
**Tipo:** Teste funcional híbrido (Python + revisão humana)  
**Referência de código do produto:** commit `98ff24b` (informado pelo script)  
**Execução:** EX01, 25/11/2026 às 14:19:47 (UTC−03:00)  
**Status global:** **REPROVADO**

## Objetivo

Verificar se o agente distingue e registra separadamente dois acontecimentos relatados em uma mesma mensagem, preservando seus respectivos contextos, sem duplicações ou omissões essenciais, e observando as instruções conversacionais vigentes.

## Escopo e pré-condições

- Execução na raiz de `aprendendo-agentes-ia`, com ambiente Python e acesso à API do agente configurados.
- Coleção ChromaDB temporária, inicialmente vazia, sem alterações intencionais no diário persistido do ambiente principal.
- Massa de teste fictícia contendo dois acontecimentos diferentes em uma única mensagem.
- Avaliação das categorias conforme o esquema vigente: `trabalho_estudos`, `relacoes`, `corpo_saude`, `rotina_lazer` e `outro`. O esquema não prevê categoria específica para animais.
- A classificação automática de emoções pela rede neural está fora do escopo desta execução; não é atribuída ao LLM.
- O critério de confirmação discreta permanece aplicável ao prompt vigente no momento do teste, independentemente de alterações propostas ainda não implementadas.

## Massa de teste

> Hoje de manhã, recebi uma notícia muito boa no trabalho: fui escolhida para participar de um projeto novo e fiquei muito feliz. Mais tarde, quando cheguei em casa, descobri que meu cachorro estava doente e fiquei preocupada.

**Acontecimentos esperados:** (1) seleção para um novo projeto no trabalho, acompanhada de felicidade declarada; (2) descoberta de que o cachorro está doente, acompanhada de preocupação declarada.

## Procedimento

1. Inicializar coleção temporária e verificar ausência de eventos prévios.
2. Enviar a mensagem única contendo os dois acontecimentos.
3. Capturar chamadas da ferramenta `registrar_momento`, argumentos, retornos e resposta conversacional.
4. Consultar a coleção após a interação, verificando quantidade, identidade, resumo, trecho original e data dos eventos.
5. Aplicar avaliação humana de fidelidade, separação dos assuntos, classificação, acolhimento, limite de perguntas e confirmação discreta.
6. Registrar resultados e encaminhamentos com base nas evidências.

**Comando de execução (raiz do repositório):**

```powershell
python QA_Equilibrium/03_Automacao/testes_hibridos.py --ct M05
```

## Registro de execução — EX01

**Data/hora:** `2026-11-25T14:19:47-03:00`  
**Commit do produto informado no JSON:** `98ff24b`  
**Resultado técnico:** **PASS (6/6)**  
**Resultado global após revisão humana:** **REPROVADO**

### Verificações automatizadas

| Critério | Resultado |
|---|---|
| `base_inicial_vazia` | **PASS** |
| `registrar_momento_chamada` | **PASS** |
| `dois_eventos_persistidos` | **PASS** |
| `dois_registros_distintos` | **PASS** |
| `trechos_originais_presentes_no_relato` | **PASS** |
| `data_hoje_em_ambos` | **PASS** |

A coleção passou de **zero para dois eventos**. Houve **duas chamadas de `registrar_momento`**, ambas retornando `Momento registrado no diário.`, e dois registros distintos persistidos. Não foram observadas tentativas rejeitadas nem duplicações nesta execução.

**Consultou memória?** `false`. A busca de acontecimentos anteriores não faz parte do objetivo deste teste.

### Resultado conversacional e avaliação humana

**Resposta observada:**

> Entendo a alegria pela novidade no trabalho e a preocupação com seu cachorro. Como você tem equilibrado esses sentimentos ao longo do dia?

| Critério | Avaliação | Fundamentação |
|---|---|---|
| Reconhecimento dos dois acontecimentos | **Conforme** | Retoma a novidade no trabalho e a preocupação com o cachorro. |
| Fidelidade às emoções declaradas | **Conforme** | Menciona alegria e preocupação, presentes no relato. |
| Tom cordial e profissional | **Conforme** | Resposta respeitosa, concisa e sem atribuição de diagnóstico. |
| Máximo de uma pergunta | **Conforme** | Uma pergunta na resposta final. |
| Ausência de diagnóstico ou alerta indevido | **Conforme** | Não apresenta diagnóstico, tratamento nem alerta de crise injustificado. |
| Confirmação discreta dos registros | **Não conforme** | Nenhum dos dois registros foi confirmado ao usuário, embora ambos tenham sido persistidos. |
| Pergunta sobre equilíbrio emocional | **Observação** | Integra os dois temas e não constitui não conformidade; sua adequação pode ser reavaliada em testes de qualidade conversacional. |

### Eventos persistidos

| Campo | Evento 1 — Novo projeto | Evento 2 — Cachorro doente |
|---|---|---|
| Resumo | Foi escolhida para participar de um projeto novo no trabalho. | Descobriu que seu cachorro estava doente, gerando preocupação. |
| Categoria | `trabalho_estudos` | `corpo_saude` |
| Data/hora informada ao armazenamento | `2026-11-25T08:00:00` | `2026-11-25T14:00:00` |
| Texto original | Primeiro trecho do relato, preservado | Segundo trecho do relato, preservado |

**Análise semântica:** os acontecimentos foram separados corretamente e os trechos originais preservados. O resumo do evento 1 omite a felicidade explicitamente declarada; já o resumo do evento 2 preserva a preocupação. A omissão no primeiro resumo não suprimiu o acontecimento principal, mas merece avaliação quanto ao efeito na recuperação posterior do contexto emocional. A categoria `trabalho_estudos` é adequada; `corpo_saude` para doença de animal de estimação é **classificação a esclarecer**, sem assumir categoria obrigatória inexistente no esquema.

**Análise temporal:** o primeiro relato informa apenas “de manhã”, e o segundo, “mais tarde, quando cheguei em casa”. Os horários exatos 08h00 e 14h00 **não foram fornecidos pelo usuário**. As datas estão corretas, mas a precisão das horas não foi demonstrada.

## Achados e encaminhamentos

| Identificador | Evidência / observação | Classificação / encaminhamento |
|---|---|---|
| **ACH-001 (recorrente)** | Os dois momentos foram persistidos; a resposta final não confirmou os registros. | **Não conformidade** em relação à instrução vigente do prompt. Reavaliar após eventual alteração efetiva e versionada do requisito. |
| **ACH-M05-001** | Horários 08h00 e 14h00 atribuídos sem informação explícita na mensagem. | **Ponto de investigação:** definir regra de representação de horário aproximado ou desconhecido; relaciona-se à investigação temporal já observada em CTs anteriores. |
| **ACH-M05-002** | A doença do cachorro recebeu a categoria `corpo_saude`, sem categoria específica para animais no esquema. | **Critério de classificação a esclarecer:** avaliar enquadramento de acontecimentos ligados a animais de estimação. |
| **ACH-M05-003** | Resumo do evento 1 preserva o projeto, mas omite a felicidade declarada. | **Ponto de avaliação semântica:** verificar impacto da omissão em memória e recuperação de contexto emocional. |

**Comportamentos positivos:** dois registros efetivos, distintos e não duplicados; trechos originais preservados; separação correta dos acontecimentos; resposta final reconhece os dois assuntos e as emoções expressas.

## Evidências

| ID | Arquivo | Conteúdo |
|---|---|---|
| E01 | [CT-M05_EX01_E01_Resultado_Hibrido.png](../02_Evidencias/CT-M05/CT-M05_EX01_E01_Resultado_Hibrido.png) | Execução no terminal, seis critérios técnicos aprovados, ferramentas chamadas e resposta final. |
| JSON | [CT-M05_20261125_141947_hibrido.json](../02_Evidencias/CT-M05/CT-M05_20261125_141947_hibrido.json) | Massa, chamadas/argumentos/retornos das ferramentas, dois registros persistidos, resultados técnicos e metadados. |

## Conclusão

**Resultado EX01: REPROVADO** — Não conformidade no critério *Confirmação discreta do registro*: o agente registrou corretamente e de forma independente os dois acontecimentos, mas não confirmou os registros ao usuário, contrariando a instrução vigente no prompt.

## Próximos passos

- Reavaliar a confirmação conversacional após eventual mudança implementada e versionada no prompt.
- Investigar como representar referências temporais sem inventar horários exatos.
- Esclarecer a categorização de acontecimentos envolvendo animais de estimação.
- Avaliar a preservação de emoções explicitamente relatadas nos resumos utilizados para memória semântica.
