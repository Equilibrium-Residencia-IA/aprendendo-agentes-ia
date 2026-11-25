# Plano e registro mestre de QA — Equilibrium / Second Challenge

**Sistema sob teste:** Agente A1 — Diário de Emoções  
**Repositório:** https://github.com/Equilibrium-Residencia-IA/aprendendo-agentes-ia  
**Código do produto:** `04_diario_emocoes/`  
**Documentação QA:** `QA_Equilibrium/`  
**Branch de contribuição:** `qa/ct-m01-m03-marcia` (atualizável com os CTs seguintes)  
**Revisão:** 25/11/2026  
**Situação:** seis CTs concluídos; dois aprovados, quatro reprovados e dois planejados.

## 1. Objetivo e escopo

Avaliar o comportamento conversacional do Agente A1, o registro e recuperação de memórias, o uso da base documental/RAG e os limites de segurança. Distinguir **chamada de ferramenta**, **retorno da ferramenta**, **dado persistido** e **resposta ao usuário**. As massas usadas nos CTs são fictícias.

**Fora do escopo até aqui:** acurácia da rede neural definitiva de classificação de emoções (o classificador provisório não serve como referência de precisão), A2/downstream e alteração do código do produto para corrigir defeitos.

## 2. Indicadores consolidados

| Indicador | Quantidade |
|---|---:|
| CTs planejados | 8 |
| CTs concluídos (ao menos uma execução avaliada) | 6 |
| Aprovados globalmente | **2** (CT-M03 e CT-M06) |
| Reprovados globalmente | **4** (CT-M01, CT-M02, CT-M04 e CT-M05) |
| Ainda não executados | **2** (CT-M07 e CT-M08) |
| Execuções manuais / híbridas | CT-M01: EX01 manual e EX02 híbrida; demais CTs executados em modo híbrido |

**Interpretação:** `PASS` técnico não equivale à aprovação global. A conclusão global é determinada com os critérios técnicos **e** a revisão humana. Achados recorrentes não são contabilizados como defeitos distintos apenas por aparecerem em CTs diferentes. Não há confirmação de tickets externos abertos.

## 3. Catálogo oficial de casos de teste

| ID | Frente | Objetivo | Resultado global | Documento |
|---|---|---|---|---|
| **CT-M01** | Memória / conversa | Registrar acontecimento marcante e confirmar discretamente | **REPROVADO** — registro confirmado no banco, sem confirmação ao usuário | [CT-M01](01_Casos_de_Testes/CT-M01.md) |
| **CT-M02** | Memória | Recuperar acontecimento em nova *thread* | **REPROVADO** — registro disponível, porém não recuperado na consulta do agente | [CT-M02](01_Casos_de_Testes/CT-M02.md) |
| **CT-M03** | Fatos estáveis | Atualizar profissão e recuperá-la em nova *thread* | **APROVADO** — fato atualizado sem contradição, com observações adicionais | [CT-M03](01_Casos_de_Testes/CT-M03.md) |
| **CT-M04** | Conversa / registro | Responder a relato cotidiano e registrar o acontecimento | **REPROVADO** — sem confirmação conversacional do registro | [CT-M04](01_Casos_de_Testes/CT-M04.md) |
| **CT-M05** | Conversa / registro | Separar dois acontecimentos em uma mensagem | **REPROVADO** — dois registros corretos, sem confirmação ao usuário | [CT-M05](01_Casos_de_Testes/CT-M05.md) |
| **CT-M06** | Recuperação semântica | Recuperar a mesma memória com duas formulações diferentes | **APROVADO** — duas recuperações corretas | [CT-M06](01_Casos_de_Testes/CT-M06.md) |
| **CT-M07** | RAG documental | Resposta conceitual fundamentada nos PDFs | **PLANEJADO** | [Planejamento](00_Planejamento/PROXIMOS_TESTES_CT04_CT08.md) |
| **CT-M08** | Segurança | Situação de risco emocional; interrupção do fluxo normal | **PLANEJADO** | [Planejamento](00_Planejamento/PROXIMOS_TESTES_CT04_CT08.md) |

**Nomenclatura:** os identificadores oficiais são sequenciais `CT-M01` a `CT-M08`; as frentes temáticas permanecem independentes do prefixo do CT.

## 4. Ambiente e preparação

| Item | Estado registrado |
|---|---|
| Ambiente | Windows, VS Code, PowerShell, Python 3.12 e `.venv` |
| Agente | LangChain/LangGraph com Groq; modelo `openai/gpt-oss-120b`, temperatura 0,6, segundo código examinado |
| Diário | ChromaDB, coleção `entradas`; isolamento temporário nos testes híbridos de eventos |
| Fatos estáveis | `fatos.json`; isolamento temporário específico no CT-M03 |
| Base documental | Seis fontes indexadas, **582 chunks** verificados na preparação |
| Proteção de credenciais | `.env` ignorado no Git; não versionar chaves, bancos locais ou perfis reais |

### Recursos documentais indexados na preparação

| Fonte | Chunks |
|---|---:|
| SCHERER_2005 | 176 |
| OPAS_ESTRESSE | 124 |
| ERQ_IDOSOS | 77 |
| ZANON_2013 | 71 |
| OLIVEIRA_2013_NORMAS | 68 |
| BIG5_MARCADORES_2012 | 66 |
| **Total** | **582** |

A indexação comprova disponibilidade dos documentos, não fidelidade de recuperação ou qualidade de respostas. A avaliação específica da base de conhecimento está prevista no CT-M07.

## 5. Metodologia e estrutura documental

1. **Preparação:** definir objetivo, massa fictícia, pré-condições e resultados esperados antes de executar. Sempre que pertinente, comprovar banco inicialmente vazio e ambiente isolado.
2. **Automação Python:** verificar fatos determinísticos, inclusive as **saídas** de tools, persistência e identidade de registros; produzir JSON com entradas, parâmetros, resultados, estado inicial/final e metadados da execução.
3. **Avaliação humana:** conferir interpretação semântica, tom, limites do prompt, qualidade dos resumos e se a resposta utilizou corretamente a memória; separar não conformidades de hipóteses e pontos a esclarecer.
4. **Conclusão:** registrar resultado global objetivo no Markdown de cada CT. `FAIL`/`PASS` da automação não substitui a análise interpretativa.
5. **Rastreabilidade:** preservar JSON por execução e print apenas quando complementar; usar caminhos relativos no Markdown. O `QA_MESTRE.md` agrega status e achados, sem duplicar os relatórios individuais.

**Convenção de artefatos:** `01_Casos_de_Testes/CT-M0x.md` (relatório único por CT); `02_Evidencias/CT-M0x/` (JSON gerado e captura, quando aplicável); `03_Automacao/testes_hibridos.py`; `04_Relatorios/` reservado a sínteses transversais, quando necessárias.

**Campos de memória nos JSONs:** `consultou_memoria`, `memoria_encontrada`, `memoria_correta` e `utilizou_memoria_na_resposta`. Valor `null` significa não avaliado ou não aplicável, e não aprovação nem reprovação automática. Chamadas de ferramentas e suas saídas devem ser diferenciadas.

**Padrão textual de conclusão:** **Resultado EX0x: APROVADO/REPROVADO — motivo determinante e comportamento observado**. Orientações impessoais nos encaminhamentos: investigar, definir, validar, corrigir e reavaliar; não atribuir ações a integrantes nominalmente. Alterações discutidas, mas não implementadas, não modificam os critérios vigentes.

## 6. Síntese das execuções homologadas

| CT | Data | Commit de produto (JSON) | Resultado técnico | Resultado global | Evidência principal |
|---|---|---|---|---|---|
| CT-M01 | 21–22/11 | `d2782ac` | EX02 **5/5 PASS** | **REPROVADO** | [CT-M01](01_Casos_de_Testes/CT-M01.md) |
| CT-M02 | 22/11 | `d2782ac` | Execução final **5 PASS / 2 FAIL** | **REPROVADO** | [CT-M02](01_Casos_de_Testes/CT-M02.md) |
| CT-M03 | 23/11 | `d2782ac` | **6/6 PASS** | **APROVADO** | [CT-M03](01_Casos_de_Testes/CT-M03.md) |
| CT-M04 | 25/11 | `98ff24b` | **5/5 PASS** | **REPROVADO** | [CT-M04](01_Casos_de_Testes/CT-M04.md) |
| CT-M05 | 25/11 | `98ff24b` | **6/6 PASS** | **REPROVADO** | [CT-M05](01_Casos_de_Testes/CT-M05.md) |
| CT-M06 | 25/11 | `98ff24b` | **7/7 PASS** | **APROVADO** | [CT-M06](01_Casos_de_Testes/CT-M06.md) |

### CT-M01 — Registro de acontecimento marcante

EX01 manual e EX02 híbrida comprovaram persistência, fidelidade do trecho original e data relativa. Ambas evidenciaram ausência de **confirmação discreta do registro** na resposta ao usuário, descumprindo a instrução do prompt vigente. Horário atribuído sem informação explícita e omissões potencialmente relevantes no resumo permanecem em avaliação.

### CT-M02 — Recuperação em nova *thread*

O registro foi semeado e recuperado por busca-controle, mas não recuperado pela consulta do agente. Na investigação, a consulta genérica `incidente de trânsito` apresentou similaridade **0,2167**, abaixo do limiar **0,35**; uma consulta específica ao acontecimento apresentou **0,8440**. O primeiro script gerava `PASS` indevido por verificar apenas chamada da tool; a validação foi corrigida para exigir recuperação efetiva. **O escopo não incluiu reinício completo do processo Python.**

### CT-M03 — Atualização de fato pessoal

O agente atualizou `profissao` de professora para coordenadora pedagógica sem manter o valor antigo como atual, e informou corretamente a profissão em outra *thread*. Chamadas registradas no histórico não equivalem automaticamente a novas gravações. Foram observadas duas tentativas distintas de `registrar_momento` durante a atualização: uma rejeitada por horário futuro e outra concluída; avaliar a pertinência desse registro adicional e o tratamento do horário.

### CT-M04 — Resposta a relato cotidiano

A caminhada foi registrada com integridade e resposta pertinente, mas faltou confirmação ao usuário (**não conformidade recorrente**). A ferramenta recusou a primeira tentativa devido a horário futuro; o agente corrigiu o argumento e conseguiu gravar um único evento. **A recuperação após erro é comportamento positivo**, sem validar a hora exata atribuída ao momento.

### CT-M05 — Dois acontecimentos em uma mensagem

Os eventos de novo projeto e cachorro doente foram separados e persistidos em dois registros distintos, ambos com trechos originais preservados. A resposta reconheceu os dois temas, mas não confirmou os registros (**não conformidade recorrente**). Investigar horas exatas atribuídas sem informação explícita, categoria `corpo_saude` para doença do animal e omissão da felicidade declarada no resumo do projeto.

### CT-M06 — Recuperação com palavras diferentes

Em duas novas consultas, o agente chamou `buscar_memoria`, recuperou o mesmo evento correto e utilizou seu conteúdo nas respostas. Similaridades diagnósticas **0,3967** e **0,3973**, ambas acima do limiar **0,35**. O resultado é positivo para essas duas formulações; uma bateria mais ampla é necessária antes de generalizar a robustez da recuperação semântica.

## 7. Registro consolidado de achados e acompanhamento

| ID / tema | Ocorrência | Classificação e próximo passo |
|---|---|---|
| **ACH-001 — Confirmação discreta ausente** | CT-M01, M04, M05 | **Não conformidade recorrente ao prompt vigente.** Reavaliar após eventual alteração implementada e versionada; não encerrar apenas porque a mudança está em discussão. |
| **ACH-002 — Horário atribuído sem evidência** | CT-M01, M03, M04, M05 | **Investigação de regra temporal:** definir representação de horário não informado ou aproximado, sem falsa precisão. |
| **ACH-003 — Preservação semântica de resumos** | CT-M01 e M05 | **Avaliação de qualidade:** investigar omissão de detalhes emocionalmente relevantes e impacto na recuperação. |
| **ACH-M02 — Recuperação semântica insuficiente para consulta genérica** | CT-M02 | **Falha funcional observada:** estudar formulação da consulta, limiar e recuperação sem alterar parâmetros sem evidência representativa. |
| **ACH-M02 — Falso PASS inicial da automação** | CT-M02 | **Instrumentação QA corrigida:** validar retorno efetivo e identidade da memória; manter histórico de tentativas. |
| **ACH-M03 — Chamadas adicionais / momento associado à mudança de profissão** | CT-M03 | **Investigação:** separar histórico de tool calls de operações realmente executadas e avaliar pertinência da gravação. |
| **ACH-M04 — Recuperação após erro** | CT-M04 | **Comportamento positivo:** erro por horário futuro seguido de correção e registro sem duplicação; preservar como alvo de regressão. |
| **ACH-M05 — Categoria do evento com animal** | CT-M05 | **Critério a definir:** avaliar `corpo_saude` para saúde de animal; esquema não contém categoria específica para animais. |
| **ACH-M06 — Proximidade do limiar** | CT-M06 | **Observação:** duas paráfrases passaram com margem limitada; ampliar consultas antes de concluir sobre robustez. |

Este consolidado registra **temas** e não substitui os IDs individuais de achados nos relatórios de cada CT. Divergências ainda em investigação não devem ser apresentadas como defeitos confirmados. Até a revisão, não há informação comprovada sobre abertura de tickets externos.

## 8. Próximos passos

- **CT-M07:** avaliar consultas conceituais ao RAG de PDFs, referências às fontes, limites de validade e ausência de extrapolação indevida.
- **CT-M08:** avaliar resposta a situação fictícia de risco emocional, interrupção do fluxo normal e não persistência do relato no mesmo turno, conforme prompt vigente.
- Consolidar decisões sobre confirmação do registro, tratamento de horários sem precisão e categorias de acontecimentos; revisar critérios após alterações efetivamente implementadas.
- Manter testes reproduzíveis em ambiente isolado; documentar limitações de amostra e variabilidade do LLM.
- Atualizar a branch de QA com resultados versionados, sem fazer merge automático na `main`.
