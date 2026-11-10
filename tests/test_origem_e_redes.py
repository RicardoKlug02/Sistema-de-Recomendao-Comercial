from datetime import date, timedelta

import pandas as pd
import pytest

from src.backend.app.models import Cliente, Fabrica, ItemVenda, Produto, Venda, Vendedor
from src.backend.app.schemas.cliente import ClienteDetalhesOut
from src.backend.app.services.analise_service import AnaliseService
from src.backend.app.services.cliente_service import ClienteService
from src.backend.app.services.excel_service import ExcelService
from src.backend.app.core.security import gerar_blind_index


REF = date(2026, 11, 9)


def registrar(db, cliente, fabrica, produto, numero, dias, vendedor=None):
    v = Venda(cliente_id=cliente.id, fabrica_id=fabrica.id, numero_pedido=numero,
              data_venda=REF-timedelta(days=dias), valor_total=10,
              vendedor_id=vendedor.id if vendedor else None)
    db.add(v); db.flush()
    if produto:
        db.add(ItemVenda(venda_id=v.id, produto_id=produto.id, quantidade=1, preco_unitario=10))
    db.flush()
    return v


def test_orion_aviso_identifica_pedido_real_da_mesma_fabrica_e_rede(db_session):
    db = db_session
    c = Cliente(razao_social='Orion SC', grupo_economico='Orion', cnpj_cpf='11111111000111')
    filial = Cliente(razao_social='Orion PR', grupo_economico=' orion ', cnpj_cpf='11111111000200')
    fora = Cliente(razao_social='Outro cliente')
    f, outra = Fabrica(nome_fantasia='Cibra'), Fabrica(nome_fantasia='Outra')
    db.add_all([c, filial, fora, f, outra]); db.flush()
    p = Produto(sku='100', nome='Produto', fabrica_id=f.id)
    db.add(p); db.flush()
    for n, dias in enumerate([150, 140, 130]):
        registrar(db, c, f, p, str(n), dias)
    registrar(db, fora, f, None, 'fora', 1)
    registrar(db, c, outra, None, 'outra-fabrica', 2)
    db.commit()
    ficha = ClienteService(db).obter_dossie_cliente(c.id, ref_date=REF)
    assert ficha['produtos_sem_confirmacao'] == []
    assert ficha['produtos_em_abandono'][0]['sku'] == '100'
    assert len(ficha['produtos_em_abandono'][0]['origem']['pedidos']) == 3

    sem_itens = registrar(db, filial, f, None, '37182', 10)
    db.commit()
    ficha = ClienteDetalhesOut.model_validate(ClienteService(db).obter_dossie_cliente(c.id, ref_date=REF)).model_dump(mode='json')
    assert ficha['produtos_em_abandono'] == []
    aviso = ficha['produtos_sem_confirmacao'][0]
    assert [v['pedido'] for v in aviso['pedidos_sem_itens']] == ['37182']
    assert aviso['pedidos_sem_itens'][0]['venda_id'] == sem_itens.id
    assert aviso['pedidos_sem_itens'][0]['cnpj_cpf'] == filial.cnpj_cpf
    assert len(aviso['origem']['pedidos']) == 3
    # O detalhe fiscal não deve herdar a falta de itens de outra filial.
    fiscal = ClienteService(db).obter_dossie_cliente(c.id, ref_date=REF, agrupar_rede=False)
    assert fiscal['produtos_sem_confirmacao'] == []


def test_rede_criada_depois_reagrupa_pedidos_antigos_e_conferencia_informa(db_session):
    db = db_session
    c = Cliente(razao_social='Gravatal', cnpj_cpf='11111111000111',
                cnpj_hash=gerar_blind_index('11111111000111'))
    filial = Cliente(razao_social='Bergler', grupo_economico='GB2')
    f = Fabrica(nome_fantasia='Cibra')
    db.add_all([c, filial, f]); db.flush()
    registrar(db, c, f, None, 'antigo', 210)
    registrar(db, filial, f, None, 'recente', 40)
    db.commit()
    assert len(AnaliseService(db, REF, REF, fabrica_id=f.id).relatorio('inativos')['linhas']) == 1
    cab = pd.DataFrame([dict(pedido='antigo', fabrica='Cibra', cliente='Gravatal', cnpj_cpf=c.cnpj_cpf,
                             data=REF-timedelta(days=210), valor_total=10, rede='GB2')])
    itens = pd.DataFrame(columns=['pedido','sku','nome_produto','quantidade','preco_unitario'])
    servico = ExcelService(db)
    antes = servico.conferir(cab, itens)
    assert antes['alteracoes_rede'][0]['rede_nova'] == 'GB2'
    servico._validar_e_salvar(cab, itens)
    assert AnaliseService(db, REF, REF, fabrica_id=f.id).relatorio('inativos')['linhas'] == []
    # Uma carga antiga sem rede não pode apagar o vínculo já definido.
    servico._validar_e_salvar(cab.assign(rede=None), itens)
    assert c.grupo_economico == 'GB2'
    assert antes['estado'] != servico.conferir(cab, itens)['estado']
    # Quando a rede efetivamente fica inativa, a evidência é a compra da outra filial.
    futuro = REF + timedelta(days=60)
    from unittest.mock import patch
    with patch('src.backend.app.services.analise_service.hoje_comercial', return_value=futuro):
        linha = AnaliseService(db, futuro, futuro, fabrica_id=f.id).relatorio('inativos')['linhas'][0]
    assert linha['cliente'] == linha['rede'] == 'GB2'
    assert linha['pedido'] == 'recente' and linha['cadastros'] == 2
    assert linha['cadastro'] == 'Bergler'


def test_filtro_vendedor_inativos_usa_ultimo_pedido_global(db_session):
    db = db_session
    c = Cliente(razao_social='Rede', grupo_economico='GB2')
    f, outra = Fabrica(nome_fantasia='Cibra'), Fabrica(nome_fantasia='Outra')
    antigo, atual = Vendedor(nome='Antigo'), Vendedor(nome='Atual')
    db.add_all([c, f, outra, antigo, atual]); db.flush()
    registrar(db, c, f, None, 'cibra', 120, antigo)
    registrar(db, c, outra, None, 'outra', 10, atual)
    db.commit()
    assert len(AnaliseService(db, REF, REF, fabrica_id=f.id, vendedor_id=atual.id).relatorio('inativos')['linhas']) == 1
    assert AnaliseService(db, REF, REF, fabrica_id=f.id, vendedor_id=antigo.id).relatorio('inativos')['linhas'] == []


def test_mesmo_cnpj_com_redes_conflitantes_rejeita_carga(db_session):
    cab = pd.DataFrame([dict(pedido=str(i), fabrica='Cibra', cliente='Cliente', cnpj_cpf='11111111000111',
                             data=REF, valor_total=10, rede=rede) for i, rede in enumerate(['GB2','Outra rede'])])
    itens = pd.DataFrame(columns=['pedido','sku','nome_produto','quantidade','preco_unitario'])
    with pytest.raises(ValueError, match='redes diferentes'):
        ExcelService(db_session)._validar_e_salvar(cab, itens)
    assert db_session.query(Venda).count() == 0


def test_api_mantem_origem_do_alerta_e_da_ficha(client, token_admin, db_session, monkeypatch):
    db = db_session
    monkeypatch.setattr('src.backend.app.services.comercial_service.hoje_comercial', lambda: REF)
    monkeypatch.setattr('src.backend.app.services.cliente_service.hoje_comercial', lambda: REF)
    c = Cliente(razao_social='Filial fiscal', grupo_economico='Orion', cnpj_cpf='11111111000111')
    f = Fabrica(nome_fantasia='Cibra')
    db.add_all([c, f]); db.flush()
    p = Produto(sku='100', nome='Produto', fabrica_id=f.id)
    db.add(p); db.flush()
    for n, dias in enumerate([150, 140, 130]):
        registrar(db, c, f, p, f'COM-ITEM-{n}', dias)
    # Outro pedido na mesma data não pode substituir a evidência do item no alerta.
    outro = Produto(sku='200', nome='Outro produto', fabrica_id=f.id)
    db.add(outro); db.flush()
    registrar(db, c, f, outro, 'OUTRO-PRODUTO', 130)
    db.commit()
    h = {'Authorization': f'Bearer {token_admin}'}
    ficha = client.get(f'/api/v1/clientes/{c.id}', headers=h)
    assert ficha.status_code == 200, ficha.text
    assert ficha.json()['origem']['rede'] == 'Orion'
    assert ficha.json()['produtos_em_abandono'][0]['origem']['pedidos'][0]['cnpj_cpf'] == c.cnpj_cpf
    alertas = client.get('/api/v1/comercial/alertas', headers=h).json()['itens'][0]['alertas']
    sinal = next(a for a in alertas if a['produto_id'] == p.id)
    assert sinal['origem']['pedidos'][0]['pedido'] == 'COM-ITEM-2'
    assert sinal['origem']['pedidos'][0]['cnpj_cpf'] == c.cnpj_cpf
