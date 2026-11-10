from datetime import date, timedelta
import io
import pandas as pd
import pytest
from sqlalchemy import func
from src.backend.app.models import Cliente, Fabrica, ItemVenda, Produto, RevisaoPedido, Venda
from src.backend.app.core.security import gerar_blind_index
from src.backend.app.services.analise_service import AnaliseService
from src.backend.app.services.associacao_service import AssociacaoService
from src.backend.app.services.cliente_service import ClienteService
from src.backend.app.services.comercial_service import ComercialService
from src.backend.app.services.excel_service import ExcelService
from src.backend.app.services.revisao_pedido_service import registrar_revisao

REF = date(2026, 11, 9)


@pytest.fixture
def base(db_session, monkeypatch):
    monkeypatch.setattr('src.backend.app.services.comercial_service.hoje_comercial', lambda: REF)
    monkeypatch.setattr('src.backend.app.services.cliente_service.hoje_comercial', lambda: REF)
    monkeypatch.setattr('src.backend.app.services.associacao_service.hoje_comercial', lambda: REF)
    c = Cliente(razao_social='Orion', grupo_economico='Orion', cnpj_cpf='11111111000111', cnpj_hash=gerar_blind_index('11111111000111'))
    f = Fabrica(nome_fantasia='Cibra')
    db_session.add_all([c, f]); db_session.flush()
    p = Produto(sku='100', nome='Produto', fabrica_id=f.id)
    db_session.add(p); db_session.flush()
    vendas = []
    for i, dias in enumerate([150, 140, 130, 5, 1]):
        v = Venda(numero_pedido=str(i), cliente_id=c.id, fabrica_id=f.id, data_venda=REF-timedelta(days=dias), valor_total=10 if i<3 else 100)
        db_session.add(v); db_session.flush()
        if i<3: db_session.add(ItemVenda(venda_id=v.id, produto_id=p.id, quantidade=1, preco_unitario=10))
        vendas.append(v)
    db_session.commit()
    return c, f, p, vendas


def test_ajuste_comissionado_conta_valor_sem_compra_nem_falso_historico_incompleto(db_session, base):
    c, f, p, vs = base
    registrar_revisao(db_session, vs[3], 'BONIFICACAO', 'Bonificação confirmada pelo responsável')
    registrar_revisao(db_session, vs[4], 'AJUSTE_COMISSIONADO', 'Comissão paga sem nova compra')
    db_session.commit()
    assert db_session.query(Venda).count() == 3
    assert db_session.query(Venda).execution_options(incluir_ajustes_comissionados=True).count() == 4
    assert db_session.query(Venda).execution_options(incluir_vendas_excluidas=True).count() == 5
    assert db_session.query(func.count(Venda.id)).scalar() == 3
    assert db_session.query(func.sum(ItemVenda.quantidade)).join(Venda).scalar() == 3
    painel = ComercialService(db_session).painel('2026-11')['indicadores']
    assert painel['venda_total'] == painel['ajustes_comissionados_valor'] == 100
    assert painel['pedidos_emitidos'] == painel['clientes_atendidos'] == painel['clientes_novos'] == 0
    assert painel['ticket_medio'] == painel['pedidos_sem_itens'] == 0
    ficha = ClienteService(db_session).obter_dossie_cliente(c.id, ref_date=REF)
    assert ficha['valor_comprado'] == 130 and ficha['pedidos_emitidos'] == 3
    assert ficha['produtos_sem_confirmacao'] == []
    assert ficha['produtos_em_abandono'][0]['produto_id'] == p.id
    assert ficha['origem']['pedidos_sem_itens'] == []
    assert ficha['origem']['ajustes_comissionados'][0]['pedido'] == vs[4].numero_pedido
    assert len(AssociacaoService(db_session)._carregar_cestas_pedidos()) == 3
    linha = AnaliseService(db_session, REF, REF, fabrica_id=f.id).relatorio('inativos')['linhas'][0]
    assert linha['dias'] == 130 and linha['pedido'] == vs[2].numero_pedido
    assert any(a['tipo'] == 'CLIENTE_INATIVO' for a in ComercialService(db_session).alertas())


def test_reimportacao_preserva_classificacao_e_identidade_do_pedido(db_session, base):
    c, f, _, vs = base
    v = vs[3]
    registrar_revisao(db_session, v, 'BONIFICACAO', 'Não gera comissão')
    db_session.commit()
    cab = pd.DataFrame([dict(pedido=v.numero_pedido, fabrica=f.nome_fantasia, cliente=c.razao_social,
                            cnpj_cpf=c.cnpj_cpf, data=v.data_venda, valor_total=50, tipo_pedido='Venda')])
    itens = pd.DataFrame(columns=['pedido','sku','nome_produto','quantidade','preco_unitario'])
    previa = ExcelService(db_session).conferir(cab, itens)
    assert previa['atualizados'] == 1
    ExcelService(db_session)._validar_e_salvar(cab, itens)
    assert db_session.query(Venda).execution_options(incluir_vendas_excluidas=True).count() == 5
    v = db_session.query(Venda).execution_options(incluir_vendas_excluidas=True).filter_by(id=v.id).one()
    assert v.classificacao == 'BONIFICACAO' and not v.considerar_analises and v.valor_total == 50


def test_importacao_mista_desconsidera_bonificacao_e_seus_itens(db_session):
    cab = pd.DataFrame([dict(pedido=str(i), fabrica='Cibra', cliente='Cliente', cnpj_cpf='11111111000111',
                            data=REF, valor_total=10, tipo_pedido=tipo) for i, tipo in enumerate(['Venda','Bonificação'])])
    itens = pd.DataFrame([dict(pedido=str(i), sku='100', nome_produto='Produto', quantidade=1, preco_unitario=10) for i in range(2)])
    s = ExcelService(db_session)
    previa = s.conferir(cab, itens, modo='sincronizar_mes', mes='2026-11')
    assert previa['processados'] == 1 and previa['valor_total'] == 10 and previa['itens'] == 1
    assert previa['pedidos_desconsiderados'][0]['tipo'] == 'Bonificação'
    s._validar_e_salvar(cab, itens)
    assert db_session.query(Venda).count() == db_session.query(ItemVenda).count() == 1


def test_arquivo_sem_tipo_nao_pode_ser_validado_como_venda(db_session):
    arquivo = io.BytesIO()
    pd.DataFrame([dict(pedido='1', fabrica='Cibra', cliente='Cliente', cnpj_cpf='11111111000111',
                       data=REF, valor_total=10)]).to_excel(arquivo, index=False)
    arquivo.seek(0)
    with pytest.raises(ValueError, match='tipo_pedido'):
        ExcelService(db_session)._limpar_excel_cabecalho(arquivo)


def test_revisao_api_autorizacao_evidencia_concorrencia_e_reversao(client, token_admin, base, db_session):
    _, _, _, vs = base
    url = f'/api/v1/cargas/pedidos/{vs[3].id}/revisao'
    assert client.get('/api/v1/cargas/pedidos').status_code == 401
    h = {'Authorization': f'Bearer {token_admin}'}
    corpo = {'classificacao': 'VENDA_DIRETA', 'motivo': 'Venda conferida', 'versao': 0}
    assert client.post(url, headers=h, json=corpo).status_code == 422
    corpo['evidencia'] = 'Pedido da fábrica conferido com responsável'
    salvo = client.post(url, headers=h, json=corpo)
    assert salvo.status_code == 200, salvo.text
    assert client.post(url, headers=h, json=corpo).status_code == 409
    corpo.update(classificacao='BONIFICACAO', motivo='Corrigido após conferir a origem', versao=salvo.json()['versao'])
    assert client.post(url, headers=h, json=corpo).status_code == 200
    r = client.get('/api/v1/cargas/pedidos?classificacao=BONIFICACAO', headers=h)
    assert r.status_code == 200 and r.json()['total'] == 1
    assert client.get('/api/v1/cargas/pedidos?classificacao=', headers=h).status_code == 200
    assert not r.json()['itens'][0]['considerar_analises']
    hist = client.get(f'/api/v1/cargas/pedidos/{vs[3].id}/historico', headers=h).json()
    assert len(hist) == 2 and hist[0]['usuario'] == 'Admin Tester'
    assert db_session.query(RevisaoPedido).count() == 2


def test_vendedor_nao_pode_revisar_pedidos(client, db_session):
    from src.backend.app.models import Usuario
    from src.backend.app.core.security import gerar_hash_senha, criar_token_acesso
    u = Usuario(nome='Vendedor', email='vendedor@teste.com', perfil='vendedor', aprovado=True, senha_hash=gerar_hash_senha('teste123'))
    db_session.add(u); db_session.commit()
    h = {'Authorization': f'Bearer {criar_token_acesso({"sub":u.email})}'}
    assert client.get('/api/v1/cargas/pedidos', headers=h).status_code == 403
    assert client.post('/api/v1/cargas/pedidos/1/revisao', headers=h,
                       json={'classificacao':'BONIFICACAO','motivo':'Não comissionado'}).status_code == 403


def test_reimportacao_com_tipo_bonificacao_corrige_registro_antigo_sem_apaga_lo(client, token_admin, base, db_session):
    c, f, _, vs = base
    cab = pd.DataFrame([dict(pedido=v.numero_pedido, fabrica=f.nome_fantasia, cliente=c.razao_social,
        cnpj_cpf=c.cnpj_cpf, data=v.data_venda, valor_total=v.valor_total,
        tipo_pedido=tipo) for v, tipo in [(vs[3], 'Bonificação'), (vs[4], 'Venda')]])
    itens = pd.DataFrame(columns=['pedido','sku','nome_produto','quantidade','preco_unitario'])
    def arquivo(df):
        b = io.BytesIO(); df.to_excel(b, index=False); return b.getvalue()
    files = {'arquivo_cabecalho': ('pedidos.xlsx', arquivo(cab)),
             'arquivo_itens': ('itens.xlsx', arquivo(itens))}
    h = {'Authorization': f'Bearer {token_admin}'}
    previa = client.post('/api/v1/cargas/conferir', headers=h, files=files)
    assert previa.status_code == 200, previa.text
    assert previa.json()['processados'] == 1
    r = client.post('/api/v1/cargas/excel', headers=h, files=files,
                    data={'vendas_comissao':'true','token_conferencia':previa.json()['token_conferencia']})
    assert r.status_code == 200, r.text
    assert r.json()['desconsiderados_por_tipo'] == 1
    assert db_session.query(Venda).execution_options(incluir_vendas_excluidas=True).count() == 5
    assert db_session.query(Venda).count() == 4
    v = db_session.query(Venda).execution_options(incluir_vendas_excluidas=True).filter_by(id=vs[3].id).one()
    assert v.classificacao == 'BONIFICACAO'
    assert db_session.query(RevisaoPedido).one().motivo == 'Tipo informado na reimportação: Bonificação.'
