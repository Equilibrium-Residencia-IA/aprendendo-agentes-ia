# CT-M06 — Recuperação semântica com formulações diferentes

**Sistema sob teste:** A1 — Diário de Emoções (`04_diario_emocoes/`)  
**Frente:** Recuperação semântica da memória de longo prazo  
**Tipo:** Teste funcional híbrido (Python + avaliação humana)  
**Referência de código do produto:** commit `98ff24b` (registrado na execução)  
**Execução:** EX01 — 25/11/2026 às 14:40:28 (UTC−03:00)  
**Status global:** **APROVADO**

## Objetivo

Verificar se uma memória previamente armazenada pode ser recuperada pelo agente a partir de **duas formulações diferentes**, sem exigir repetição literal do resumo persistido; avaliar a chamada de `buscar_memoria`, a recuperação do registro correto e seu uso fiel nas respostas.

## Escopo e pré-condições

- Ambiente Python e configuração de acesso ao modelo disponíveis na raiz do repositório.
- Coleção ChromaDB **temporária**, inicialmente vazia, com massa sintética inserida diretamente pelo mecanismo de armazenamento.
- Um único acontecimento persistido antes das consultas, preservado ao final (sem duplicação).
- Duas consultas independentes em novas threads. O teste **não comprova reinício do processo** nem mede recuperação em grande volume de memórias.
- Limiar de similaridade do produto informado no JSON: `0.35`.
- O teste não avalia classificação da rede neural nem precisão estatística da recuperação.

## Massa de teste

**Memória semeada (resumo indexado):**

> Quase atropelou uma senhora ao voltar do trabalho, freou a tempo e ficou assustado.

**Categoria:** `outro`  
**Data de ocorrência:** `2026-11-24T14:40:21`

**Consulta 1:**

> Você lembra quando precisei frear bruscamente porque uma pedestre surgiu na minha frente? O que aconteceu?

**Consulta 2:**

> Você recorda aquele susto que levei dirigindo na volta para casa? Pode me lembrar do episódio?

## Procedimento

1. Inicializar uma coleção temporária e verificar ausência de eventos prévios.
2. Semear um acontecimento e verificar sua recuperação em busca-controle.
3. Iniciar uma nova thread para cada formulação, enviar a pergunta e registrar as chamadas de ferramenta e suas saídas.
4. Verificar se ambas as consultas recuperaram o evento esperado e se o registro não foi duplicado.
5. Comparar as respostas com os dados recuperados e registrar a avaliação humana.

**Comando (raiz do repositório):**

```powershell
python QA_Equilibrium/03_Automacao/testes_hibridos.py --ct M06
```

## Registro da execução — EX01

**Execução em:** `2026-11-25T14:40:28-03:00`  
**Resultado técnico:** **PASS (7/7)**  
**Avaliação humana:** **Conforme**  
**Resultado global:** **APROVADO**

### Verificações automatizadas

| Critério | Resultado |
|---|---|
| `base_inicial_vazia` | **PASS** |
| `registro_semeado` | **PASS** |
| `busca_controle_recupera_registro` | **PASS** |
| `consultou_memoria_nas_duas` | **PASS** |
| `memoria_encontrada_nas_duas` | **PASS** |
| `memoria_correta_nas_duas` | **PASS** |
| `registro_nao_duplicado` | **PASS** |

**Consultou memória?** `true`, nas duas tentativas.  
**Memória encontrada?** `true`, nas duas tentativas.  
**Memória correta?** `true`, nas duas tentativas.  
**Utilizou memória na resposta?** **Sim — confirmado na avaliação humana**. O JSON original mantém `null` nesse campo porque o script não executa essa avaliação semântica automaticamente.

O estado da coleção permaneceu em **um registro** após a semeadura e as duas consultas.

### Resultados por formulação

| Item | Tentativa 1 | Tentativa 2 |
|---|---|---|
| Consulta enviada à ferramenta | `frear bruscamente pedestre` | `susto dirigindo na volta para casa` |
| Score diagnóstico (sem filtros) | **0,3967** | **0,3973** |
| Limiar mínimo | 0,35 | 0,35 |
| Resultado da ferramenta | Memória correta encontrada | Memória correta encontrada |
| Resposta utiliza a memória | Conforme | Conforme |

**Resposta da tentativa 1:**

> Você precisou frear bruscamente quando uma pedestre surgiu à sua frente, quase a atropelou, mas conseguiu parar a tempo, ficando assustado. Como você se sentiu depois desse episódio?

**Resposta da tentativa 2:**

> Na volta para casa, você quase atropelou uma senhora, freou a tempo e ficou assustado. Como você tem lidado com esse sentimento desde então?

### Revisão humana

| Critério | Avaliação | Fundamentação |
|---|---|---|
| Recuperação contextual na primeira formulação | **Conforme** | Retoma a quase colisão, a frenagem e o susto. |
| Recuperação contextual na segunda formulação | **Conforme** | Retoma o incidente com a senhora, a frenagem e o susto. |
| Ausência de fatos inventados | **Conforme** | Não introduz acontecimento novo ou informação incompatível com o relato e as perguntas. |
| Uso adequado da memória na resposta | **Conforme** | As duas respostas refletem o evento efetivamente retornado pela ferramenta. |
| Adequação conversacional | **Conforme** | Respostas profissionais, concisas e com no máximo uma pergunta em cada tentativa. |
| Integridade do armazenamento | **Conforme** | Um evento antes e depois das consultas; sem duplicação. |

## Achados e observações técnicas

**ACH-M06-001 — Sensibilidade ao limiar de similaridade (observação, não defeito confirmado).** As duas consultas recuperaram a memória, porém os scores diagnósticos (`0,3967` e `0,3973`) ficaram relativamente próximos do limite `0,35`. A execução demonstra sucesso com essas duas formulações, mas **não garante robustez para outras paráfrases**. Avaliar futuramente um conjunto mais amplo de consultas e diferentes condições de indexação.

**Comportamento positivo:** o agente chamou `buscar_memoria` nas duas tentativas, obteve o acontecimento correto e respondeu de maneira coerente, sem solicitar repetição do relato nem produzir registros adicionais.

**Limite de interpretação:** os scores citados são de **consultas diagnósticas sem filtros**, embora os argumentos reais da ferramenta não tenham incluído filtros na segunda tentativa e na primeira tenham apresentado apenas `consulta`. O resultado funcional é confirmado adicionalmente pelas saídas efetivas de `buscar_memoria`, que retornaram o registro com relevância arredondada para `0.40`.

## Evidências

| ID | Arquivo | Finalidade |
|---|---|---|
| E01 | [CT-M06_EX01_E01_Resultado_Hibrido.png](../02_Evidencias/CT-M06/CT-M06_EX01_E01_Resultado_Hibrido.png) | Terminal: duas consultas, resultados positivos, scores de diagnóstico e respostas do agente. |
| JSON | [CT-M06_20261125_144028_hibrido.json](../02_Evidencias/CT-M06/CT-M06_20261125_144028_hibrido.json) | Dados completos de execução, parâmetros reais das ferramentas, saídas, pré-condições e verificações automáticas. Arquivo gerado localmente pelo script. |

## Conclusão

**Resultado EX01: APROVADO** — O agente recuperou corretamente o mesmo acontecimento em duas consultas com formulações diferentes e utilizou as informações nas respostas, atendendo às verificações técnicas e aos critérios de qualidade conversacional definidos para o caso.

## Próximos passos

- Ampliar a bateria de paráfrases e medir a sensibilidade da recuperação ao limiar configurado.
- Registrar a revisão humana no próprio relatório; não interpretar o `null` do JSON como reprovação, pois indica campo não avaliado automaticamente.
- Avaliar posteriormente a recuperação entre reinicializações do processo e com bases maiores, fora do escopo desta execução.
