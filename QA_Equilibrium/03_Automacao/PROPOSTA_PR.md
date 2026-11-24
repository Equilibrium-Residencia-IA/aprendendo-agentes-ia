# Apresentação da contribuição — QA híbrido (CT-M01 a CT-M03)

## Objetivo

Documentar um piloto de testes híbridos do Agente A1 (Diário de Emoções), reunindo verificações reproduzíveis em Python, evidências estruturadas e revisão humana.

## Entregas

- `testes_hibridos.py`: execução dos CT-M01 (registro), CT-M02 (recuperação semântica) e CT-M03 (atualização de fato estável).
- `README.md`: instruções e limitações.
- `../01_Casos_de_Testes/`: relatórios com critérios, resultados e achados.
- `../02_Evidencias/`: saídas JSON, prints de testes e preparação do ambiente.
- `../QA_MESTRE.md`: controle de cobertura e status.

## Resultados do piloto

- **CT-M01:** reprovado na avaliação global por ausência da confirmação discreta do registro; verificações técnicas de persistência aprovadas.
- **CT-M02:** reprovado por não recuperar memória relevante; a consulta `incidente de trânsito` teve score 0,2167, inferior ao limiar 0,35 em diagnóstico controlado.
- **CT-M03:** aprovado para atualização/persistência do fato, com observações sobre uso de ferramentas e repetição de histórico.

## Limites

- Evidências correspondem a execuções específicas, não a avaliação estatística abrangente.
- CT-M02 não testa reinício do processo Python.
- O status técnico automatizado não substitui a avaliação humana.
- Nenhuma alteração ao código do produto é proposta neste pacote.
