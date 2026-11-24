# Plano e registro mestre de QA — Equilibrium / Second Challenge

**Sistema sob teste:** Agente A1 — Diário de Emoções  
**Repositório:** https://github.com/Equilibrium-Residencia-IA/aprendendo-agentes-ia  
**Pasta de referência:** `04_diario_emocoes/`  
**Versão/commit de referência:** `d2782ac` (hash abreviado)  
**Responsável pelos testes:** _preencher_  
**Última revisão do documento:** 2026-11-23  
**Situação:** Preparação concluída; CT-M01 e CT-M02 reprovados; CT-M03 aprovado com pontos de investigação; demais CTs pendentes

## 1. Objetivo

Avaliar o comportamento conversacional do A1, o registro e a recuperação de memórias, o uso da base de conhecimento/RAG e os limites de segurança e ética, com entradas fictícias e evidências rastreáveis. Distinguir **resposta exibida**, **ferramenta chamada**, **registro persistido** e **informação recuperada**.

## 2. Escopo atual

- **Agente (CT-A):** respostas contextualizadas, uso correto de ferramentas, limites conversacionais.
- **Memórias (CT-M):** registro de eventos, fatos estáveis, persistência, recuperação e não duplicação.
- **RAG (CT-R):** recuperação semântica do diário e da base de PDFs, fontes, relevância e ausência de extrapolação.
- **Segurança (CT-S):** risco, privacidade, não diagnóstico e respeito aos limites de apoio emocional.

**Fora do escopo inicial:** medir a acurácia da rede neural definitiva de emoções enquanto o classificador provisório estiver ativo; avaliar o A2/downstream; alterar o código-fonte do sistema sob teste.

## 3. Ambiente e rastreabilidade

| Campo | Registro |
|---|---|
| Data/hora da preparação | 18 e 21/11/2026 (horário local); EX01 em 21/11 |
| Sistema operacional | Windows; VS Code / PowerShell |
| Python / ambiente virtual | Python 3.12; `.venv` ativo |
| Branch e hash do commit | `main` / `d2782ac` (abreviado) |
| Comando de execução | `python 04_diario_emocoes/main.py` |
| Base de dados / perfil de teste | ChromaDB local em `04_diario_emocoes/state/chroma`; coleção `entradas` com 0 eventos antes da EX01; coleção `conhecimento` com 582 chunks. EX02 utilizou coleção temporária inicialmente vazia, com verificação automatizada. Utilizar exclusivamente dados fictícios. |
| Modelo LLM / parâmetros | `openai/gpt-oss-120b`, temperatura 0.6 (configuração do código analisado; primeira resposta conversacional obtida em EX01) |
| Versões relevantes das dependências | `pip check` sem inconsistências antes da atualização; `pypdf==7.1.1` instalado após o pull; demais versões a registrar quando necessário. |
| Evidências da execução | `02_Evidencias/<ID>/` (prints da EX01 e JSON validado da EX02) |

### 3.1. Checklist de preparação — 21/11/2026

| Verificação | Resultado observado | Situação |
|---|---|---|
| Atualização do repositório | `git pull --ff-only`: `707b187..d2782ac`, fast-forward, 16 commits recebidos, sem conflitos reportados | Concluída |
| Ambiente virtual e dependências | `.venv` ativo; atualização instalou `pypdf-7.1.1` | Concluída |
| Configuração da API | Variável `GROQ_API_KEY` localizada pelo Python; `git check-ignore .env` retornou `.env` | Configurada; primeira interação concluída sem erro aparente |
| Recursos documentais | Seis PDFs e `FONTES_E_LINKS.md` presentes localmente, conforme inventário de recursos | Confirmada presença por nomes visíveis |
| Indexação do RAG | Seis fontes e 582 chunks confirmados diretamente no ChromaDB | Concluída |
| Inicialização do A1 | Saudação inicial e prompt `Você:` exibidos sem erro aparente | Concluída |
| Pré-condição CT-M01 | Consulta direta à coleção `entradas`: `Total de eventos: 0` | Atendida |

### 3.2. Inventário do RAG de conhecimento

| Fonte (`fonte_id`) | Chunks |
|---|---:|
| SCHERER_2005 | 176 |
| OPAS_ESTRESSE | 124 |
| ERQ_IDOSOS | 77 |
| ZANON_2013 | 71 |
| OLIVEIRA_2013_NORMAS | 68 |
| BIG5_MARCADORES_2012 | 66 |
| **Total** | **582** |

A consulta direta ao banco confirmou a presença das seis fontes indexadas, sem divergência de cobertura em relação ao inventário de recursos. A presença dos chunks não comprova a qualidade da recuperação semântica ou a fidelidade das respostas do agente.

### 3.3. Evidências de preparação

| ID | Evidência | Resultado demonstrado |
|---|---|---|
| ENV-E01 | [ENV_E01_Indexacao_RAG.png](02_Evidencias/00_Preparacao_Ambiente/ENV_E01_Indexacao_RAG.png) | Execução da indexação e listagem dos recursos locais |
| ENV-E02 | [ENV_E02_Consulta_ChromaDB.png](02_Evidencias/00_Preparacao_Ambiente/ENV_E02_Consulta_ChromaDB.png) | 582 chunks distribuídos em seis fontes |
| ENV-E03 | [ENV_E03_Inicializacao_Agente.png](02_Evidencias/00_Preparacao_Ambiente/ENV_E03_Inicializacao_Agente.png) | Inicialização e saudação fixa do A1; não comprova chamada ao LLM |
| ENV-E04 | [ENV_E04_Base_Eventos_Vazia.png](02_Evidencias/00_Preparacao_Ambiente/ENV_E04_Base_Eventos_Vazia.png) | Coleção de eventos com zero registros antes do CT-M01 |

## 4. Catálogo de CTs

| ID | Frente | Título | Status | Documento | Defeito |
|---|---|---|---|---|---|
| CT-A01 | Agente | Resposta a relato cotidiano | Não executado | A detalhar | — |
| CT-A02 | Agente | Dois acontecimentos em uma mensagem | Não executado | A detalhar | — |
| CT-M01 | Memória | Registro de acontecimento marcante | Reprovado (EX01 e EX02) | [CT-M01](01_Casos_de_Testes/CT-M01.md) | ACH-001; ACH-002/003 em análise |
| CT-M02 | Memória | Recuperação em nova conversa | **Reprovado (EX01 híbrida)** | [CT-M02](01_Casos_de_Testes/CT-M02.md) | ACH-M02-001; ACH-M02-002 (automação corrigida); ACH-M02-003 |
| CT-M03 | Memória | Atualização de fato pessoal estável | **Aprovado (EX01 híbrida), com pontos de investigação** | [CT-M03](01_Casos_de_Testes/CT-M03.md) | ACH-M03-001; ACH-M03-002 (investigar) |
| CT-R01 | RAG | Recuperação sem repetir palavras originais | Não executado | A detalhar | — |
| CT-R02 | RAG | Resposta conceitual baseada nos PDFs | Não executado | A detalhar | — |
| CT-S01 | Segurança | Situação de risco e interrupção do fluxo normal | Não executado | A detalhar | — |

## 5. Padrão de execução e evidência

Para cada CT, concentrar a análise e a conclusão em `01_Casos_de_Testes/CT-<ID>.md`, sem criar relatório individual duplicado. Registrar: **objetivo, referência ao comportamento esperado, pré-condições, massa de teste, passos, resultados esperados, resultados obtidos, evidências, status, observações e defeitos relacionados**.

A automação grava um JSON por execução em `02_Evidencias/<ID>/`. O `QA_MESTRE.md` registra apenas indicadores, status e links; `04_Relatorios/` fica reservado a sínteses consolidadas. Prints são opcionais e devem acrescentar informação.

As respostas livres da IA podem variar. Não exigir uma frase literal, exceto quando isso constituir requisito. Analisar semanticamente os critérios e repetir execuções quando apropriado; registrar cada tentativa de forma independente. A execução automatizada não substitui a revisão humana de comportamento sensível.

**Níveis de evidência:**

1. **Interface/terminal:** o que o usuário viu.
2. **Ferramentas (tools):** o que foi chamado e com quais argumentos (sem dados sensíveis).
3. **Persistência:** registros efetivos no ChromaDB ou no mecanismo correspondente.
4. **Recuperação:** documentos/eventos recuperados, scores, filtros e, quando houver, traces.

## 6. Registro de sessões

| Sessão | Data | Commit | CTs | Resumo | Evidências |
|---|---|---|---|---|---|
| ENV-01 | 21/11/2026 | `d2782ac` | Nenhum | Preparação do ambiente concluída; CT-M01 pronto para iniciar | ENV-E01 a ENV-E04 |
| EX01 (manual) | 21/11/2026 | `d2782ac` | CT-M01 | Evento registrado; confirmação conversacional ausente; horário e resumo em investigação | E01, E02, E04, E05 |
| EX02 (híbrida, validada) | 22/11/2026 | `d2782ac` | CT-M01 | Cinco verificações técnicas aprovadas; revisão humana identificou novamente a ausência de confirmação | [JSON EX02](02_Evidencias/CT-M01/CT-M01_EX02.json) |
| EX01 (híbrida, validada) | 22/11/2026 | `d2782ac` | CT-M02 | Script corrigido: 5 critérios aprovados, 2 reprovados; memória disponível na busca-controle, não recuperada pelo agente; resultado global reprovado | [CT-M02](01_Casos_de_Testes/CT-M02.md) |

| EX01 (híbrida, validada) | 23/11/2026 | `d2782ac` | CT-M03 | Atualização e recuperação de profissão em nova *thread*; 6/6 critérios PASS; chamadas adicionais sob investigação | [CT-M03](01_Casos_de_Testes/CT-M03.md) |

## 7. Pontos a confirmar nas próximas execuções

- Base local de eventos vazia confirmada em EX01 e base temporária vazia comprovada em EX02; avaliar isolamento de perfil/fatos e reinicialização segura para os próximos CTs. Consulta direta ao ChromaDB já validada.
- Arquivo de entrada, branch e commit de referência identificados; capturar chamadas e argumentos das tools em execuções futuras; primeira resposta do LLM observada.
- Para CTs de RAG, estabelecer registros/documentos esperados (*ground truth*) e critérios para considerar a recuperação relevante.
- Para cenários de segurança, usar dados fictícios; validar critérios de aceitação de segurança.

## 8. Registro de defeitos e decisões

Documentar cada problema confirmado em `03_Defeitos/`; não classificar divergências sem evidências suficientes como defeitos definitivos. Decisões de escopo e mudanças de critérios devem ser registradas aqui com data e responsável.


### Decisões registradas em 21/11/2026

- Escopo restrito ao Diário de Emoções (`04_diario_emocoes`); exercícios didáticos excluídos.
- Abordagem híbrida adotada: coleta e verificações técnicas em Python; avaliação conversacional documentada no próprio CT; Phoenix permanece como ferramenta candidata.
- Documentação em Markdown, com referências relativas às evidências.
- EX01 manual e EX02 híbrida do CT-M01 concluídas; manter a memória da EX01 sem exclusões. CT-M02 executado após correção dos critérios de recuperação; resultado funcional reprovado.

## 9. Consolidação — CT-M01 (EX01 e EX02, 21–22/11/2026)

**Indicadores:** 8 CTs planejados; 3 CTs executados (CT-M01, CT-M02 e CT-M03); 1 aprovado; 2 reprovados; 5 não executados; 1 não conformidade observada, 2 pontos a esclarecer/investigar; 0 tickets de defeito abertos.

| ID | Achado | Situação |
|---|---|---|
| ACH-001 | Agente não confirmou o registro, apesar de um evento gravado | Não conformidade observada com o prompt; investigar e corrigir a ausência de confirmação |
| ACH-002 | Data correta, mas atribuição de 17h sem horário fornecido | Definir tratamento de horário desconhecido |
| ACH-003 | Resumo preserva núcleo, mas omite a preocupação prolongada em ambas as execuções; a travessia repentina foi omitida na EX01 | Avaliar relevância e impacto na recuperação, ainda não medido |

Na EX01, o banco passou de 0 para 1 evento e o relato original foi preservado; categoria `outro`, conflito `false` e classificação provisória `fear` (0.8). Não houve captura direta das tools. Na EX02, cinco verificações automáticas passaram, com base temporária inicialmente vazia e chamada de `registrar_momento` capturada. A revisão humana constatou novamente ausência de confirmação, além de omissão da preocupação persistente no resumo. A categoria `trabalho_estudos` aplicada na EX02 é uma observação a investigar, sem diagnóstico de defeito. O evento da EX01 permanece como massa de teste possível para CT-M02.


Detalhamento da execução e evidências: [CT-M01](01_Casos_de_Testes/CT-M01.md).

## 10. Consolidação — CT-M02 (22/11/2026)

**Resultado EX01: REPROVADO** — A memória previamente semeada estava disponível na busca-controle, porém a consulta do agente não recuperou o acontecimento. O script corrigido registrou `FAIL` nas verificações de memória encontrada e memória correta, impedindo aprovação indevida apenas pela chamada da ferramenta.

**Instrumentação:** registrar `consultou_memoria` em todas as execuções, distinguir memória encontrada e memória correta e preservar argumentos das ferramentas para análise. O uso correto da memória na resposta requer análise semântica e não é inferido apenas da chamada.

**Encaminhamentos:** investigar estratégias de consulta semântica e o limiar com consultas representativas; preservar a distinção entre falha de recuperação e causa definitiva. O escopo contempla nova *thread* com base temporária, não reinício do processo.

Detalhamento, evidências e histórico diagnóstico: [CT-M02](01_Casos_de_Testes/CT-M02.md).


## 11. Consolidação — CT-M03 (23/11/2026)

**Resultado EX01: APROVADO** — O fato pessoal foi registrado e atualizado na mesma chave (`profissao`) e a informação vigente, `coordenadora pedagógica`, foi utilizada corretamente em nova *thread*. A verificação técnica registrou 6/6 critérios aprovados; o isolamento utilizou armazenamento temporário.

**Pontos de investigação:** a captura do segundo turno contém chamada histórica de `lembrar_fato` com ID já registrado no primeiro turno; ajustar a instrumentação para evitar duplicações de histórico. Houve duas tentativas de `registrar_momento` (uma rejeitada como futura e uma aceita); avaliar a atribuição de horário e a pertinência do registro como acontecimento. `consultou_memoria=false` é esperado para fatos estáveis disponibilizados pelo prompt; não se exige busca no diário.

Detalhamento e evidências: [CT-M03](01_Casos_de_Testes/CT-M03.md).
