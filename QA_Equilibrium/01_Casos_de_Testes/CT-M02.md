# CT-M02 — Recuperação de acontecimento em nova conversa

**Sistema sob teste:** A1 — Diário de Emoções (`04_diario_emocoes/`)  
**Tipo:** Teste funcional híbrido (Python + revisão humana)  
**Referência de código:** branch `main`, commit `d2782ac`  
**Data:** 22/11/2026 (horário local, UTC−03:00)  
**Status global:** **REPROVADO**

## Objetivo

Verificar se o agente recupera e utiliza corretamente um acontecimento previamente persistido quando questionado em uma nova *thread* conversacional, sem duplicar o registro.

## Escopo e limitações

A execução prepara uma entrada fictícia em coleção temporária do ChromaDB e inicia uma nova *thread* para a consulta. **Não valida o encerramento e reinício do processo Python** nem a recuperação do registro da EX01 manual do CT-M01. A busca-controle consulta diretamente o armazenamento; a busca do agente depende dos argumentos enviados à ferramenta `buscar_memoria`.

## Pré-condições e massa de teste

| Item | Critério / valor |
|---|---|
| Coleção | Temporária, isolada; inicial com zero registros |
| Preparação | `armazenamento.gravar()` com um registro sintético |
| Resumo persistido | “Quase atropelou uma senhora ao voltar do trabalho, freou a tempo e ficou assustado.” |
| Categoria | `outro` |
| Relato original | Relato fictício de quase atropelamento com susto persistente |
| Pergunta ao agente | “Você se lembra daquele incidente de trânsito que eu contei? O que aconteceu?” |
| Limiar semântico | `MIN_SCORE = 0.35` |

## Procedimento

1. Abrir uma coleção temporária e verificar ausência de entradas anteriores.
2. Persistir uma entrada fictícia utilizando `armazenamento.gravar()`.
3. Executar busca-controle direta para comprovar a recuperabilidade da massa.
4. Enviar a pergunta em uma nova *thread* ao agente.
5. Registrar chamadas, argumentos, respostas das ferramentas e resposta final.
6. Validar recuperação efetiva e correta da memória, além da ausência de duplicação.
7. Confrontar os resultados automáticos com a resposta exibida e documentar o resultado global.

**Comando:** `python QA_Equilibrium/03_Automacao/testes_hibridos.py --ct M02`

## Registro de execução — EX01 híbrida

### Verificações automatizadas na execução final

| Verificação | Resultado |
|---|---|
| `base_inicial_vazia` | **PASS** |
| `registro_semeado` | **PASS** |
| `busca_controle_recupera_registro` | **PASS** |
| `buscar_memoria_chamada` | **PASS** |
| `memoria_encontrada` | **FAIL** |
| `memoria_correta` | **FAIL** |
| `registro_nao_duplicado` | **PASS** |

**Status técnico gerado pelo script corrigido: `FAIL`.** A massa estava disponível e era recuperável na busca-controle, mas a ferramenta chamada pelo agente não retornou a entrada esperada.

### Consulta e resposta observadas

- **Consultou memória?** `true` — chamada de `buscar_memoria` registrada.
- **Memória encontrada?** `false` — retorno “Nenhum momento relacionado encontrado no diário.”
- **Memória correta?** `false` — não houve registro recuperado.
- **Utilizou memória na resposta?** `false` — a resposta afirmou não haver registro; a resposta foi consistente com a saída da ferramenta, mas não satisfez o objetivo da recuperação.
- **Resposta final da execução validada:** “Não tenho registro desse incidente no diário. Gostaria de contar novamente o que aconteceu?”

### Diagnóstico complementar de similaridade

As medições abaixo provêm de execução diagnóstica anterior, com a mesma massa semântica, e **não representam novas medições da execução final**.

| Consulta diagnóstica | Similaridade | Resultado com limiar 0,35 |
|---|---:|---|
| `incidente de trânsito` | 0,2167 | Descartado |
| `quase atropelou uma senhora ao voltar do trabalho` | 0,8440 | Recuperado |

Nessa execução diagnóstica, o registro dos argumentos de `buscar_memoria` confirmou `consulta="incidente de trânsito"`, sem filtros de data ou categoria. O descarte abaixo de 0,35 explica o retorno vazio naquela tentativa. A execução final confirma que a busca-controle recuperou a massa, mas a busca do agente não; a explicação por limiar deve permanecer associada à tentativa em que a pontuação foi medida.

### Revisão humana

| Critério | Avaliação |
|---|---|
| Existência do registro antes da consulta | Conforme (verificação automatizada) |
| Busca-controle do registro | Conforme (verificação automatizada) |
| Acionamento de `buscar_memoria` | Conforme |
| Recuperação do acontecimento correto | **Não conforme** |
| Fidelidade da resposta ao retorno da ferramenta | Conforme: respondeu à ausência reportada pela ferramenta |
| Utilização do acontecimento na resposta | **Não conforme**, pois a recuperação não ocorreu |
| Invenção de detalhes do evento | Não observada na resposta final |
| Persistência sem duplicação | Conforme |

**Resultado EX01: REPROVADO** — O agente consultou a memória, mas não recuperou o acontecimento previamente registrado. A busca-controle comprovou a disponibilidade do evento no ChromaDB; a ferramenta utilizada pelo agente retornou ausência de memória relacionada. O objetivo de recuperação em nova *thread* não foi atendido.

## Achados e encaminhamentos técnicos

| ID | Observação | Encaminhamento |
|---|---|---|
| ACH-M02-001 | Recuperação não ocorreu apesar da disponibilidade do registro na busca-controle | Investigar a formulação das consultas, avaliar robustez frente a referências genéricas e revalidar a recuperação semântica |
| ACH-M02-002 | Na instrumentação inicial, o script gerava `PASS` ao verificar somente a chamada da ferramenta e a ausência de duplicação | **Corrigido na automação de QA:** exigir confirmação da memória encontrada e correta; preservar os resultados anteriores como histórico da investigação |
| ACH-M02-003 | Consulta diagnóstica genérica teve similaridade 0,2167, abaixo do limiar 0,35; consulta específica obteve 0,8440 | Avaliar, mediante conjunto representativo de consultas, os critérios de busca e de calibração do limiar antes de alterar parâmetros do produto |

Não há evidência de erro de persistência ou de aplicação incorreta do limiar. A falha observada refere-se ao **resultado funcional de recuperação**, sem causa de implementação definitiva estabelecida.

## Evidências

| Identificação | Arquivo | Finalidade |
|---|---|---|
| EX01-E01 | [CT-M02_EX01_E01_Resultado_Hibrido.png](../02_Evidencias/CT-M02/CT-M02_EX01_E01_Resultado_Hibrido.png) | Captura do terminal com `FAIL` técnico, critérios e resposta final |
| EX01-JSON | JSON da última execução gerado em `02_Evidencias/CT-M02/` | Resultados técnicos completos e rastreabilidade da execução; preservar arquivo original gerado localmente |

**Nota de rastreabilidade:** o script manteve o identificador `hibrida-EX01` nas tentativas de investigação. A execução final homologada é a captura com as sete verificações listadas acima. As execuções anteriores permanecem material diagnóstico e não devem ser confundidas com a homologação final.

## Encerramento e próximos passos

- Investigar estratégias de formulação de consulta e a recuperação de referências genéricas ao acontecimento.
- Avaliar o limiar de similaridade com um conjunto de consultas representativas; não ajustar o parâmetro com base em um único relato.
- Manter a validação de retorno efetivo e identidade da memória na automação, além do registro padronizado de consulta/resultado.
- Reexecutar o CT após a definição e implementação de eventuais melhorias, com identificador de tentativa único.
- Planejar cenário independente para reinício completo do processo Python, fora do escopo desta execução.
