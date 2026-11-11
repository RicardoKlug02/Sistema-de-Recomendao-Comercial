from datetime import date
import pytest
from src.backend.app.models import Venda
from src.backend.app.api.cliente import VisitaEntrada
from src.backend.app.services.visita_service import preparar_visita
from src.backend.app.services.conferencia_carga import conferir_base
from tests.test_usabilidade import carteira


def test_conferencia_final_persistida_no_historico(client, token_admin):
    from tests.test_operacao import cabecalhos, itens, xlsx
    h = {'Authorization': f'Bearer {token_admin}'}
    arquivos = {'arquivo_cabecalho': ('pedidos.xlsx', xlsx(cabecalhos())),
                'arquivo_itens': ('itens.xlsx', xlsx(itens()))}
    previa = client.post('/api/v1/cargas/conferir', headers=h, files=arquivos, data={"mes": "2026-08"})
    r = client.post('/api/v1/cargas/excel', headers=h, files=arquivos,
                    data={'token_conferencia': previa.json()['token_conferencia'], 'vendas_comissao': 'true', 'mes': '2026-08', 'confirmar_sincronizacao': 'true'})
    assert r.status_code == 200, r.text
    base = r.json()['conferencia_base']
    assert base['pedidos_compra'] == 2 and base['linhas_itens'] == 1
    assert base['valor_comissionado'] == r.json()['valor_arquivo'] == 300
    assert base['pendentes_sem_itens'] == 1
    historico = client.get('/api/v1/cargas/historico', headers=h).json()
    assert historico[0]['conferencia_base'] == base


def test_visita_respeita_rede_fabrica_selecao_e_evidencia(client, token_admin, db_session, carteira):
    cs, fs, ps = carteira
    entrada = VisitaEntrada(fabrica_id=fs[0].id, produtos_ids=[ps[0].id])
    dados = preparar_visita(db_session, cs[1].id, entrada)
    produto = dados['secoes'][0]['itens'][0]
    assert len(dados['cadastros']) == 2
    assert produto['sku'] == '21053' and produto['preco'] == 10
    assert produto['ultima']['pedido'] == '2'
    assert produto['ultima']['cliente'] == 'Filial 0'
    assert not preparar_visita(db_session, cs[1].id, entrada.model_copy(update={'agrupar_rede': False}))['secoes'][0]['itens']
    assert not preparar_visita(db_session, cs[0].id, entrada.model_copy(update={'fabrica_id': fs[1].id}))['secoes'][0]['itens']
    caminho = f'/api/v1/clientes/{cs[0].id}/visita.pdf'
    assert client.post(caminho, json={}).status_code == 401
    h = {'Authorization': f'Bearer {token_admin}'}
    r = client.post(caminho, headers=h, json=entrada.model_dump())
    assert r.status_code == 200 and r.content.startswith(b'%PDF')
    assert r.headers['cache-control'] == 'no-store'
    assert client.post(caminho, headers=h, json={'abandono': False, 'recompra': False}).status_code == 422
    assert client.post(caminho, headers=h, json={'produtos_ids': []}).status_code == 422
    assert client.post('/api/v1/clientes/999999/visita.pdf', headers=h, json={}).status_code == 404


def test_conferencia_separa_compra_ajuste_bonificacao_e_periodos(db_session, carteira):
    cs, fs, _ = carteira
    for numero, valor, considerar, nova in [('ajuste', 150, True, False), ('bonus', 90, False, True), ('sem-item', 30, True, True)]:
        db_session.add(Venda(numero_pedido=numero, cliente_id=cs[0].id, fabrica_id=fs[0].id,
            data_venda=date(2026, 1, 25), valor_total=valor, considerar_analises=considerar, nova_compra=nova))
    resumo = conferir_base(db_session, {'modo': 'sincronizar_mes', 'mes': '2026-01'})
    assert resumo['inicio'] == '2026-01-01' and resumo['fim'] == '2026-01-31'
    assert resumo['valor_comissionado'] == 240
    assert resumo['pedidos_compra'] == 4 and resumo['ajustes_comissionados'] == 1
    assert resumo['fora_analises'] == 1 and resumo['pendentes_sem_itens'] == 1
    assert resumo['linhas_itens'] == 3


@pytest.mark.parametrize('situacao', ['RECOMPRA_REALIZADA', 'PRODUTO_DESCONTINUADO'])
def test_resultado_exige_referencia_preserva_sinais_e_historico(client, token_admin, carteira, situacao):
    cs, _, _ = carteira
    h = {'Authorization': f'Bearer {token_admin}'}
    antes = client.get('/api/v1/comercial/alertas', headers=h).json()
    grupo = antes['itens'][0]
    caminho = f'/api/v1/comercial/alertas/{cs[0].id}'
    entrada = {'situacao': situacao, 'assinatura': grupo['assinatura'], 'versao': 0}
    assert client.post(caminho+'/acompanhamento', headers=h, json=entrada).status_code == 422
    entrada['motivo'] = 'Pedido 123, fábrica EV, código 21053 - confirmado com o responsável'
    assert client.post(caminho+'/acompanhamento', headers=h, json=entrada).status_code == 200
    depois = client.get('/api/v1/comercial/alertas?situacao='+situacao, headers=h).json()
    assert depois['total_alertas'] == antes['total_alertas']
    assert depois['itens'][0]['acompanhamento']['situacao'] == situacao
    assert client.get(caminho+'/historico', headers=h).json()[0]['motivo'] == entrada['motivo']
