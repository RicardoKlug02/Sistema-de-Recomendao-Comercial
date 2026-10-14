from datetime import date, timedelta
import pytest
from src.backend.app.models import Cliente, Fabrica, Produto, Venda, ItemVenda
from src.backend.app.services.relatorios_service import RelatoriosService
from src.backend.app.services.cliente_service import ClienteService
from src.backend.app.services.comercial_service import ComercialService
from src.backend.app.services.colaborativo_service import ColaborativoService


@pytest.fixture
def compras_rede(db_session):
    a, b = Fabrica(nome_fantasia='Fábrica A'), Fabrica(nome_fantasia='Fábrica B')
    c1, c2, c3 = [Cliente(razao_social=n, grupo_economico=r) for n, r in [('Matriz', 'Rede A'), ('Filial', 'Rede A'), ('Fora da rede', 'Rede B')]]
    db_session.add_all([a, b, c1, c2, c3]); db_session.flush()
    p1, p2 = Produto(sku='COD-1', nome='Produto A', fabrica_id=a.id), Produto(sku='COD-1', nome='Produto B', fabrica_id=b.id)
    db_session.add_all([p1, p2]); db_session.flush()
    def comprar(cliente, produto, dias, preco, pedido, item=True):
        v=Venda(numero_pedido=pedido, cliente_id=cliente.id, fabrica_id=produto.fabrica_id, data_venda=date.today()-timedelta(days=dias), valor_total=preco*2)
        db_session.add(v); db_session.flush()
        if item: db_session.add(ItemVenda(venda_id=v.id, produto_id=produto.id, quantidade=2, preco_unitario=preco))
    comprar(c1,p1,90,10,'1'); comprar(c2,p1,5,12,'2'); comprar(c1,p2,80,7,'3')
    comprar(c3,p1,1,99,'4'); comprar(c2,p1,0,20,'5',False)
    db_session.commit()
    return a,b,c1,c2,c3


def test_ultimo_preco_e_data_da_mesma_compra_em_toda_rede(db_session, compras_rede):
    a,b,*_=compras_rede
    r=RelatoriosService(db_session).produtos_rede('Rede A')
    assert r['total']==2 and r['clientes']==2 and r['pedidos_sem_itens']==1
    assert {p['fabrica'] for p in r['produtos']}=={'Fábrica A','Fábrica B'}
    atual=next(p for p in r['produtos'] if p['fabrica']=='Fábrica A')
    assert atual['ultimo_preco']==12 and atual['pedido']=='2' and atual['cliente']=='Filial'
    assert atual['ultima_compra']==(date.today()-timedelta(days=5)).isoformat()
    filtrado=RelatoriosService(db_session).produtos_rede('Rede A',b.id)
    assert filtrado['total']==1 and filtrado['produtos'][0]['ultimo_preco']==7
    with pytest.raises(ValueError): RelatoriosService(db_session).produtos_rede('Inexistente')


def test_filtro_fabrica_consistente_na_lista_ficha_e_painel(client,token_admin,db_session,compras_rede):
    a,b,c1,c2,c3=compras_rede
    h={'Authorization':f'Bearer {token_admin}'}
    lista=client.get(f'/api/v1/comercial/clientes?fabrica_id={b.id}',headers=h).json()
    assert lista['total']==1 and lista['itens'][0]['id']==c1.id
    busca=client.get(f'/api/v1/comercial/clientes?termo=Filial&fabrica_id={b.id}',headers=h).json()
    assert busca['total']==0
    ficha=ClienteService(db_session).obter_dossie_cliente(c1.id,agrupar_rede=True,fabrica_id=b.id)
    assert ficha['valor_comprado']==14 and ficha['pedidos_emitidos']==1
    assert {r['fabrica_id'] for r in ficha['resumo_fabricas']}=={b.id}
    mes=(date.today()-timedelta(days=80)).strftime('%Y-%m')
    painel=ComercialService(db_session).painel(mes,fabrica_id=b.id)
    assert painel['indicadores']['venda_total']==14


def test_cliente_inativo_com_tres_fabricas_ocupa_um_card(client,token_admin,db_session):
    c=Cliente(razao_social='Cliente inativo'); db_session.add(c); db_session.flush()
    fs=[Fabrica(nome_fantasia='Fábrica '+str(i)) for i in range(3)]
    db_session.add_all(fs); db_session.flush()
    for i,f in enumerate(fs): db_session.add(Venda(numero_pedido=str(i),cliente_id=c.id,fabrica_id=f.id,data_venda=date.today()-timedelta(days=120),valor_total=100))
    db_session.commit()
    h={'Authorization':f'Bearer {token_admin}'}
    r=client.get('/api/v1/comercial/alertas',headers=h).json()
    assert r['total']==1 and r['total_alertas']==4
    assert len(r['itens'][0]['alertas'])==4
    r=client.get('/api/v1/comercial/alertas?tipo=FABRICA_INATIVA',headers=h).json()
    assert r['total']==1 and r['total_alertas']==3
    r=client.get(f'/api/v1/comercial/alertas?fabrica_id={fs[0].id}',headers=h).json()
    assert r['total']==1 and r['total_alertas']==2


def test_relatorios_pdf_autenticados(client,token_admin,compras_rede):
    assert client.get('/api/v1/relatorios/redes').status_code==401
    h={'Authorization':f'Bearer {token_admin}'}
    redes=client.get('/api/v1/relatorios/redes',headers=h).json()
    assert redes[0]=={'nome':'Rede A','clientes':2}
    pdf=client.get('/api/v1/relatorios/produtos-rede/pdf?rede=Rede%20A',headers=h)
    assert pdf.status_code==200 and pdf.headers['content-type']=='application/pdf'
    assert pdf.content.startswith(b'%PDF')
    assert client.get('/api/v1/relatorios/produtos-rede?rede=Inexistente',headers=h).status_code==422


def test_consumo_agregado_sem_misturar_clientes_sem_documento(db_session):
    f=Fabrica(nome_fantasia='Fábrica'); c1=Cliente(razao_social='Um'); c2=Cliente(razao_social='Dois')
    db_session.add_all([f,c1,c2]); db_session.flush()
    p=Produto(sku='COD',nome='Produto',fabrica_id=f.id); db_session.add(p); db_session.flush()
    for i,c in enumerate([c1,c1,c2]):
        v=Venda(numero_pedido=str(i),cliente_id=c.id,fabrica_id=f.id,data_venda=date.today(),valor_total=10)
        db_session.add(v); db_session.flush(); db_session.add(ItemVenda(venda_id=v.id,produto_id=p.id,quantidade=2,preco_unitario=5))
    db_session.commit()
    perfis=ColaborativoService(db_session)._carregar_perfis_consumo()
    assert perfis[f'cliente:{c1.id}'][p.id]==4
    assert perfis[f'cliente:{c2.id}'][p.id]==2