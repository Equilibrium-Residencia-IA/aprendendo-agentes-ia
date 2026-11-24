"""Execução híbrida experimental do Diário de Emoções (CT-M01 / CT-M02 / CT-M03).

Executar da raiz do repositório aprendendo-agentes-ia:
 python QA_Equilibrium/03_Automacao/testes_hibridos.py --ct M01
 python QA_Equilibrium/03_Automacao/testes_hibridos.py --ct M02
 python QA_Equilibrium/03_Automacao/testes_hibridos.py --ct M03

Usa apenas dados fictícios, coleção temporária de eventos e uma thread nova por CT.
M02 verifica recuperação a partir de uma memória semeada, não reinício do processo.
Não altera o código do produto. Resposta semântica exige revisão humana.
"""
import argparse
import json
import os
import sys
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from uuid import uuid4

PASTA_TESTES = Path(__file__).resolve().parent.parent
REPO = Path.cwd()
MODULO = REPO / '04_diario_emocoes'
EVIDENCIAS = PASTA_TESTES / '02_Evidencias'
RELATO = ('Ontem, quando voltava do trabalho, quase atropelei uma senhora que atravessou a rua de repente. '
          'Consegui frear a tempo, mas fiquei muito assustado e passei o restante do dia pensando no que poderia ter acontecido.')


def confirmar_ambiente():
    if not (MODULO / 'agente.py').is_file():
        raise SystemExit('ERRO: execute na raiz do repositorio aprendendo-agentes-ia (04_diario_emocoes ausente).')
    if not os.getenv('GROQ_API_KEY'):
        from dotenv import load_dotenv
        load_dotenv(REPO / '.env')
    if not os.getenv('GROQ_API_KEY'):
        raise SystemExit('ERRO: GROQ_API_KEY ausente no ambiente/.env (nao a imprima).')
    sys.path.insert(0, str(MODULO))


def info_repositorio():
    import subprocess
    try:
        return subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD'], cwd=REPO, text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        return 'nao_identificado'


def conversar(agente, pergunta, thread_id=None):
    from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
    conf = {'configurable': {'thread_id': thread_id or ('qa-' + uuid4().hex)}}
    retorno = agente.invoke({'messages': [HumanMessage(content=pergunta)]}, conf)
    chamadas_detalhadas = [
        {'nome': chamada['name'], 'argumentos': chamada.get('args', {}),
         'id': chamada.get('id')}
        for mensagem in retorno['messages'] if isinstance(mensagem, AIMessage)
        for chamada in (mensagem.tool_calls or [])
    ]
    chamadas = [item['nome'] for item in chamadas_detalhadas]
    ferramentas = [
        {'nome': mensagem.name, 'saida': str(mensagem.content),
         'id_chamada': getattr(mensagem, 'tool_call_id', None)}
        for mensagem in retorno['messages'] if isinstance(mensagem, ToolMessage)
    ]
    return {'mensagem_enviada': pergunta, 'resposta': str(retorno['messages'][-1].content),
            'chamadas': chamadas, 'chamadas_detalhadas': chamadas_detalhadas,
            'ferramentas': ferramentas}


def avaliar_consulta_memoria(conversa, resumo_esperado=None):
    """Verifica uso e resultado da ferramenta; não infere correção apenas pela chamada.

    A qualidade semântica da resposta permanece sujeita à revisão humana.
    """
    consultou = 'buscar_memoria' in conversa['chamadas']
    saidas = [f['saida'] for f in conversa['ferramentas'] if f['nome'] == 'buscar_memoria']
    # Sem consulta: resultado não avaliável (null no JSON, não false positivo).
    if not consultou:
        return {'consultou_memoria': False, 'memoria_encontrada': None,
                'memoria_correta': None, 'utilizou_memoria_na_resposta': None}
    encontrou = any(
        '- ' in linha and ' | relevância ' in saida
        for saida in saidas for linha in saida.splitlines()
    )
    # Sem memória recuperada, não há objeto para avaliar como correto.
    correta = (any(resumo_esperado in saida for saida in saidas)
               if encontrou and resumo_esperado else None)
    return {'consultou_memoria': True, 'memoria_encontrada': encontrou,
            'memoria_correta': correta, 'utilizou_memoria_na_resposta': None}


def ct_m01(agente, tools, armazenamento, colecao):
    antes = colecao.count()
    conversa = conversar(agente, RELATO)
    registros = armazenamento.listar(colecao)
    novos = registros[antes:]
    esperado_dia = (datetime.now() - timedelta(days=1)).date().isoformat()
    checks = {
        'base_inicial_vazia': antes == 0,
        'registrar_momento_chamada': 'registrar_momento' in conversa['chamadas'],
        'um_evento_registrado': colecao.count() - antes == 1,
        'trecho_original_igual': len(novos) == 1 and novos[0]['trecho_original'] == RELATO,
        'data_ontem': len(novos) == 1 and novos[0]['ocorrido_em'][:10] == esperado_dia,
    }
    return {'ct': 'CT-M01', 'execucao': 'hibrida-EX02', 'status_tecnico': 'PASS' if all(checks.values()) else 'FAIL',
            'checks': checks, 'conversa': conversa,
            **avaliar_consulta_memoria(conversa),
            'registros': [{'id': x['id'], 'resumo': x['resumo'], 'ocorrido_em': x['ocorrido_em'],
                           'categoria': x['categoria'], 'trecho_original': x['trecho_original']}
                          for x in novos],
            'revisao_humana_pendente': ['fidelidade_do_resumo', 'confirmacao_discreta_do_registro',
                                       'acolhimento', 'ausencia_de_diagnostico', 'maximo_uma_pergunta',
                                       'ausencia_de_alerta_indevido']}


def ct_m02(agente, tools, armazenamento, colecao):
    from datetime import datetime as dt
    from uuid import uuid4 as uuid
    antes = colecao.count()
    data_evento = (dt.now() - timedelta(days=1)).replace(microsecond=0).isoformat()
    entrada = {'id': str(uuid()), 'registrado_em': dt.now().replace(microsecond=0).isoformat(),
               'ocorrido_em': data_evento,
               'resumo': 'Quase atropelou uma senhora ao voltar do trabalho, freou a tempo e ficou assustado.',
               'trecho_original': RELATO, 'categoria': 'outro', 'envolve_conflito': False,
               'emocoes': []}
    armazenamento.gravar(colecao, entrada)
    apos_semeadura = colecao.count()
    # Busca-controle independente do LLM. Confirma que o registro pode ser recuperado
    # pelo armazenamento no limiar configurado, antes da conversa com o agente.
    controle = armazenamento.buscar(colecao, entrada['resumo'])
    controle_ok = any(e['id'] == entrada['id'] for e, _ in controle)
    consulta = 'Você se lembra daquele incidente de trânsito que eu contei? O que aconteceu?'
    conversa = conversar(agente, consulta)
    memoria = avaliar_consulta_memoria(conversa, entrada['resumo'])
    depois = colecao.count()
    checks = {
        'base_inicial_vazia': antes == 0,
        'registro_semeado': apos_semeadura - antes == 1,
        'busca_controle_recupera_registro': controle_ok,
        'buscar_memoria_chamada': memoria['consultou_memoria'],
        'memoria_encontrada': memoria['memoria_encontrada'] is True,
        'memoria_correta': memoria['memoria_correta'] is True,
        'registro_nao_duplicado': depois == apos_semeadura,
    }
    return {'ct': 'CT-M02', 'execucao': 'hibrida-EX01',
            'escopo': 'nova thread com memoria de evento semeada; NAO testa reinicio do processo',
            'status_tecnico': 'PASS' if all(checks.values()) else 'FAIL',
            'checks': checks, 'conversa': conversa, **memoria,
            'registro_semeado': {'id': entrada['id'], 'resumo': entrada['resumo'],
                                 'ocorrido_em': entrada['ocorrido_em']},
            'busca_controle': {'recuperou_registro': controle_ok,
                               'scores': [round(score, 4) for e, score in controle if e['id'] == entrada['id']]},
            'revisao_humana_pendente': ['resposta_recupera_o_evento_correto',
                                       'nao_inventa_detalhes', 'resposta_coerente_com_registro']}



def ct_m03(agente, tools, armazenamento, colecao, fatos, pasta_fatos):
    """Atualizacao de fato estavel, com arquivo JSON totalmente isolado.

    T1 e T2 compartilham a thread; T3 usa nova thread para testar persistencia.
    Os fatos sao lidos diretamente do arquivo temporario antes/depois de cada turno.
    """
    antes = fatos.carregar_fatos(pasta_fatos)
    thread_atualizacao = 'qa-m03-' + uuid4().hex
    primeira = conversar(agente, 'Sou professora em uma escola.', thread_atualizacao)
    depois_primeira = fatos.carregar_fatos(pasta_fatos)
    segunda = conversar(agente, 'Mudei de profissao. Agora sou coordenadora pedagogica.', thread_atualizacao)
    depois_segunda = fatos.carregar_fatos(pasta_fatos)
    terceira = conversar(agente, 'Qual e minha profissao atual?')  # nova thread
    depois_terceira = fatos.carregar_fatos(pasta_fatos)

    # Os valores e as chaves sao decididos pelo agente, por isso registramos
    # os estados efetivos e evitamos aprovar apenas por chamadas de ferramenta.
    import unicodedata
    def normalizar(texto):
        sem_acentos = ''.join(c for c in unicodedata.normalize('NFD', texto.lower())
                              if unicodedata.category(c) != 'Mn')
        return sem_acentos.strip()

    iniciais = {k for k, v in depois_primeira.items() if 'professor' in normalizar(v)}
    atualizados = {k for k, v in depois_segunda.items()
                   if 'coordenadora pedagogica' in normalizar(v)}
    chamadas_primeira = [x for x in primeira['chamadas_detalhadas'] if x['nome'] == 'lembrar_fato']
    chamadas_segunda = [x for x in segunda['chamadas_detalhadas'] if x['nome'] == 'lembrar_fato']
    checks = {
        'fatos_iniciais_vazios': antes == {},
        'fato_inicial_registrado': bool(iniciais) and bool(chamadas_primeira),
        'atualizacao_da_mesma_chave': bool(iniciais & atualizados) and bool(chamadas_segunda),
        'profissao_anterior_nao_atual': not any(
            'professor' in normalizar(v) and 'coordenadora pedagogica' not in normalizar(v)
            for v in depois_segunda.values()),
        'profissao_atual_persistida': bool(atualizados) and depois_terceira == depois_segunda,
        'nenhum_fato_duplicado': len(depois_segunda) == len(depois_primeira) == 1,
    }
    conversas = [primeira, segunda, terceira]
    # Campo presente em todos os CTs; nao pressupor que buscar_memoria deva
    # ser usada para fatos estaveis (o prompt injeta fatos no inicio de cada turno).
    memoria = [avaliar_consulta_memoria(c) for c in conversas]
    return {
        'ct': 'CT-M03', 'execucao': 'hibrida-EX01',
        'escopo': 'atualizacao de fato estavel em JSON temporario; consulta final em nova thread',
        'status_tecnico': 'PASS' if all(checks.values()) else 'FAIL',
        'checks': checks,
        'conversas': conversas,
        'consultou_memoria': any(m['consultou_memoria'] for m in memoria),
        'memoria_encontrada': None, 'memoria_correta': None,
        'utilizou_memoria_na_resposta': None,
        'consulta_memoria_por_turno': memoria,
        'estado_fatos': {'antes': antes, 'depois_primeira': depois_primeira,
                         'depois_atualizacao': depois_segunda, 'depois_nova_thread': depois_terceira},
        'revisao_humana_pendente': ['resposta_final_informa_profissao_atual',
                                   'nao_apresenta_profissao_anterior_como_atual',
                                   'nao_inventa_informacoes', 'adequacao_conversacional'],
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--ct', choices=['M01', 'M02', 'M03'], required=True)
    parser.add_argument('--verificar', action='store_true', help='Somente confere ambiente, sem chamar Groq')
    args = parser.parse_args()
    confirmar_ambiente()
    if args.verificar:
        print('OK: pasta do produto e GROQ_API_KEY encontradas (chave nao testada).')
        return
    import tools
    import armazenamento
    import agente as modulo_agente
    # Evita injetar perfis ou fatos antigos do usuario local nos prompts de QA.
    modulo_agente._perfil = lambda: ''
    with tempfile.TemporaryDirectory(
        prefix='qa_equilibrium_',
        ignore_cleanup_errors=True,
    ) as pasta:
        colecao = armazenamento.abrir_colecao(Path(pasta))
        tools.colecao = colecao
        try:
            if args.ct == 'M01':
                resultado = ct_m01(modulo_agente.agente, tools, armazenamento, colecao)
            elif args.ct == 'M02':
                resultado = ct_m02(modulo_agente.agente, tools, armazenamento, colecao)
            else:
                import fatos
                pasta_fatos = Path(pasta) / 'fatos_isolados'
                salvar_original = fatos.salvar_fato
                perfil_original = modulo_agente._perfil

                def salvar_fato_isolado(chave, valor, pasta=None):
                    return salvar_original(chave, valor, pasta=pasta_fatos)

                # Tools usa fatos.salvar_fato em tempo de chamada. Prompt usa
                # modulo_agente._perfil, assim lemos e gravamos no mesmo JSON.
                fatos.salvar_fato = salvar_fato_isolado
                modulo_agente._perfil = lambda: (
                    '\n\nFatos que a pessoa te contou (use-os naturalmente):\n'
                    + fatos.formatar_fatos(pasta_fatos)
                    if fatos.carregar_fatos(pasta_fatos) else ''
                )
                try:
                    resultado = ct_m03(modulo_agente.agente, tools, armazenamento,
                                       colecao, fatos, pasta_fatos)
                finally:
                    fatos.salvar_fato = salvar_original
                    modulo_agente._perfil = perfil_original
        finally:
            tools.colecao = None
    resultado['executado_em'] = datetime.now().astimezone().isoformat(timespec='seconds')
    resultado['commit'] = info_repositorio()
    resultado['observacao'] = 'status_tecnico nao representa aprovacao final; exige revisao humana'
    pasta_evidencias = EVIDENCIAS / resultado['ct']
    pasta_evidencias.mkdir(parents=True, exist_ok=True)
    destino = pasta_evidencias / f"{resultado['ct']}_{datetime.now():%Y%m%d_%H%M%S}_hibrido.json"
    destino.write_text(json.dumps(resultado, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f"\n{resultado['ct']} | verificacoes tecnicas: {resultado['status_tecnico']}")
    for criterio, ok in resultado['checks'].items():
        print(f"  {'OK' if ok else 'FALHOU'} {criterio}")
    print('Consultou memoria:', resultado['consultou_memoria'])
    print('Memoria encontrada:', resultado['memoria_encontrada'])
    print('Memoria correta:', resultado['memoria_correta'])
    if 'conversas' in resultado:
        for i, turno in enumerate(resultado['conversas'], 1):
            print(f'Turno {i} | tools:', ', '.join(turno['chamadas']) or '(nenhuma)')
            print(f'Turno {i} | resposta:', turno['resposta'])
        print('Fatos apos atualizacao:', resultado['estado_fatos']['depois_atualizacao'])
    else:
        print('Tools chamadas:', ', '.join(resultado['conversa']['chamadas']) or '(nenhuma)')
        print('Resposta:', resultado['conversa']['resposta'])
    print('Revisao humana: PENDENTE')
    print('Resultado completo:', destino)


if __name__ == '__main__':
    main()
