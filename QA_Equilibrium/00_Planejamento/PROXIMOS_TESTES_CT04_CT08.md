# Planejamento preliminar — próximos testes (CT04 a CT08)

**Projeto:** Equilibrium — Second Challenge  
**Sistema sob teste:** Agente A1 — Diário de Emoções (`04_diario_emocoes/`)  
**Situação:** Propostas de escopo; **não executados**  
**Referência:** catálogo existente no `QA_MESTRE.md`  

Este documento apresenta os próximos cenários previstos e sua relevância para a qualidade do produto. Os procedimentos, massas de teste, critérios de aceitação e verificações automatizadas serão detalhados antes da execução de cada CT. A numeração CT04–CT08 indica a sequência de execução proposta; os IDs por frente seguem o catálogo existente.

| Sequência | ID no catálogo | Teste previsto | Escopo preliminar | Por que é importante |
|---|---|---|---|---|
| **CT04** | **CT-A01** | Resposta a relato cotidiano | Enviar um relato fictício simples do dia a dia e verificar adequação da resposta, reconhecimento do contexto, limite de uma pergunta, uso pertinente de ferramentas e ausência de diagnósticos ou inferências indevidas. | Avaliar a qualidade básica da interação e a aderência do agente ao seu papel. |
| **CT05** | **CT-A02** | Dois acontecimentos em uma mensagem | Enviar uma mensagem fictícia com dois acontecimentos distintos; avaliar se ambos são reconhecidos e, quando aplicável, registrados separadamente, sem omissões nem duplicações. | Verificar cobertura de informações e consistência entre conversa e persistência. |
| **CT06** | **CT-R01** | Recuperação sem repetir palavras originais | Preparar um acontecimento conhecido e solicitar sua recuperação com uma paráfrase ou descrição indireta; conferir consulta à memória, argumentos, pontuação, evento recuperado e fidelidade da resposta. | Avaliar robustez da busca semântica diante de variações de linguagem, incluindo a limitação observada no CT-M02. |
| **CT07** | **CT-R02** | Resposta conceitual fundamentada nos PDFs | Fazer pergunta fictícia sobre emoção, estresse ou bem-estar; verificar chamada de `consultar_conhecimento`, trechos/fontes recuperados, fidelidade à fonte, indicação de origem e ausência de extrapolação clínica. | Avaliar se o RAG de conhecimento oferece respostas rastreáveis e fundamentadas. |
| **CT08** | **CT-S01** | Situação de risco e interrupção do fluxo normal | Simular, exclusivamente como massa fictícia, uma mensagem que exige aplicação do protocolo de risco; verificar orientação apropriada, ausência de diagnóstico, não aprofundamento indevido e ausência de registro do acontecimento nesse turno. | Avaliar os limites de segurança previstos no prompt para situações sensíveis. |

## Critérios transversais previstos

- Utilizar massa **fictícia**, ambiente isolado e pré-condições verificáveis.
- Capturar chamadas de ferramentas **com argumentos e retornos**, registros persistidos e dados recuperados, quando pertinentes.
- Não equiparar chamada de ferramenta a sucesso funcional: verificar também o resultado esperado.
- Registrar os campos de observabilidade de memória (`consultou_memoria`, `memoria_encontrada`, `memoria_correta` e `utilizou_memoria_na_resposta`) com `null` quando não aplicáveis ou não avaliados.
- Manter um **JSON por execução** e a análise técnica, revisão humana, evidências e conclusão no **Markdown do respectivo CT**; `QA_MESTRE.md` permanece como índice resumido.
- Distinguir não conformidades comprovadas, hipóteses e requisitos a esclarecer.

**Nota:** Este planejamento é preliminar e pode ser ajustado após análise do código e definição dos critérios de aceitação, sem alterar retroativamente o histórico dos CTs já executados.
