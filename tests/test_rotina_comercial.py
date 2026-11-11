from datetime import date, timedelta

import pytest

from src.backend.app.models import Cliente, Fabrica, ItemVenda, Produto, RegraNegocio, Venda


REF = date(2026, 11, 11)


@pytest.fixture(autouse=True)
def data_fixa(monkeypatch):
    for modulo in ('services.comercial_service', 'services.excel_service', 'api.comercial'):
        monkeypatch.setattr(f'src.backend.app.{modulo}.hoje_comercial', lambda: REF)


def pedido(db, cliente, fabrica, numero, dias, produto=None, valor=10):
    venda = Venda(cliente_id=cliente.id, fabrica_id=fabrica.id, numero_pedido=numero,
                  data_venda=REF-timedelta(days=dias), valor_total=valor)
    db.add(venda)
    db.flush()
    if produto:
        db.add(ItemVenda(venda_id=venda.id, produto_id=produto.id, quantidade=1, preco_unitario=10))
        db.flush()


def test_filtro_de_fabrica_nao_impede_salvar_acompanhamento(client, token_admin, db_session):
    rede = Cliente(razao_social='Rede de teste')
    fabricas = [Fabrica(nome_fantasia=f'Fábrica {i}') for i in range(2)]
    db_session.add_all([rede, *fabricas])
    db_session.flush()
    for f in fabricas:
        produto = Produto(sku='ABC', nome='Produto', fabrica_id=f.id)
        db_session.add(produto)
        db_session.flush()
        pedido(db_session, rede, f, '1', 80, produto)
        pedido(db_session, rede, f, '2', 65, produto)
    db_session.commit()
    h = {'Authorization': f'Bearer {token_admin}'}
    base = '/api/v1/comercial/alertas'
    total = client.get(base, headers=h).json()['itens'][0]
    grupo = client.get(f'{base}?fabrica_id={fabricas[0].id}', headers=h).json()['itens'][0]
    assert len(grupo['alertas']) < len(total['alertas'])
    assert grupo['assinatura'] == total['assinatura']
    r = client.post(f'{base}/{rede.id}/acompanhamento', headers=h,
                    json={'situacao': 'CONTATADO', 'motivo': 'Visita realizada',
                          'assinatura': grupo['assinatura'], 'versao': 0})
    assert r.status_code == 200, r.text


def test_restricao_nao_apaga_compra_e_reativacao_substitui_segundo_pedido(client, token_admin, db_session):
    ativo = Cliente(razao_social='Cliente ativo')
    inativo = Cliente(razao_social='Cliente inativo')
    livre = Fabrica(nome_fantasia='Livre')
    restrita = Fabrica(nome_fantasia='Restrita')
    db_session.add_all([ativo, inativo, livre, restrita])
    db_session.flush()
    pedido(db_session, ativo, livre, '1', 95)
    pedido(db_session, ativo, restrita, '2', 10)
    pedido(db_session, inativo, livre, '3', 90)
    db_session.add(RegraNegocio(tipo='RESTRICAO', fabrica_id=restrita.id,
                               inicio=REF-timedelta(days=5), motivo='Teste'))
    db_session.commit()
    h = {'Authorization': f'Bearer {token_admin}'}
    grupos = client.get('/api/v1/comercial/alertas', headers=h).json()['itens']
    por_cliente = {g['cliente_id']: {a['tipo'] for a in g['alertas']} for g in grupos}
    assert por_cliente[ativo.id] == {'FABRICA_INATIVA'}
    assert por_cliente[inativo.id] == {'CLIENTE_INATIVO', 'FABRICA_INATIVA'}


def test_api_recusa_atualizacao_avulsa_e_mes_aberto(client, token_admin, db_session):
    h = {'Authorization': f'Bearer {token_admin}'}
    files = {k: ('teste.xlsx', b'arquivo nao deve ser lido')
             for k in ('arquivo_cabecalho', 'arquivo_itens')}
    for endpoint, dados in [('conferir', {}), ('excel', {'token_conferencia': 'invalido',
                              'vendas_comissao': 'true', 'confirmar_sincronizacao': 'true'})]:
        base = '/api/v1/cargas/' + endpoint
        for escopo in ({}, {'modo': 'atualizar', 'mes': '2026-10'}, {'mes': '2026-11'}):
            r = client.post(base, headers=h, files=files, data={**dados, **escopo})
            assert r.status_code == 422, r.text
    assert db_session.query(Venda).count() == 0


def test_volume_ordena_clientes_e_fabricas_sem_perder_retorno_do_dia(client, token_admin, db_session):
    grande, menor = [Cliente(razao_social=n) for n in ('Rede maior', 'Rede menor')]
    a, b = [Fabrica(nome_fantasia=n) for n in ('Fábrica A', 'Fábrica B')]
    db_session.add_all([grande, menor, a, b])
    db_session.flush()
    pedido(db_session, grande, a, '1', 77, valor=1000)
    pedido(db_session, grande, b, '2', 100, valor=20)
    pedido(db_session, menor, a, '3', 110, valor=50)
    pedido(db_session, menor, b, '4', 100, valor=200)
    pedido(db_session, menor, b, '5', 450, valor=10000)
    db_session.add(Venda(cliente_id=menor.id, fabrica_id=b.id, numero_pedido='Ajuste',
                         data_venda=REF, valor_total=10000, nova_compra=False))
    db_session.commit()
    h = {'Authorization': f'Bearer {token_admin}'}
    caminho = '/api/v1/comercial/alertas'
    grupos = client.get(caminho, headers=h).json()['itens']
    assert [(g['cliente_id'], g['volume_compras_12m']) for g in grupos] == [(grande.id, 1020), (menor.id, 250)]
    assert [s['fabrica_id'] for s in grupos[0]['alertas']] == [a.id, b.id]
    filtrados = client.get(f'{caminho}?fabrica_id={b.id}', headers=h).json()['itens']
    assert [(g['cliente_id'], g['volume_compras_12m']) for g in filtrados] == [(menor.id, 200), (grande.id, 20)]
    r = client.post(f'{caminho}/{menor.id}/acompanhamento', headers=h, json={
        'situacao': 'AGUARDANDO_RETORNO', 'proximo_contato': REF.isoformat(),
        'assinatura': grupos[1]['assinatura'], 'versao': 0,
    })
    assert r.status_code == 200, r.text
    hoje = client.get(f'{caminho}?rotina=true', headers=h).json()['itens']
    assert [g['cliente_id'] for g in hoje] == [menor.id, grande.id]
