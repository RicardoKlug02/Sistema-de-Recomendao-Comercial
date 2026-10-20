from datetime import date, datetime, timedelta
import pytest
from src.backend.app.models import Cliente, Fabrica, Produto, Venda, ItemVenda, Importacao, AcaoAlerta
from src.backend.app.services.cliente_service import ClienteService

REF = date(2026, 10, 18)


@pytest.fixture
def carteira(db_session, monkeypatch):
    monkeypatch.setattr('src.backend.app.services.comercial_service.hoje_comercial', lambda: REF)
    monkeypatch.setattr('src.backend.app.api.comercial.hoje_comercial', lambda: REF)
    monkeypatch.setattr('src.backend.app.services.cliente_service.hoje_comercial', lambda: REF)
    cs = [Cliente(razao_social='Filial '+str(i), grupo_economico='Rede de teste', estado='SC') for i in range(2)]
    fs = [Fabrica(nome_fantasia=n) for n in ['Fábrica EV', 'Outra fábrica']]
    db_session.add_all(cs+fs); db_session.flush()
    ps = [Produto(sku='21053',nome='Produto de teste',fabrica_id=f.id) for f in fs]
    db_session.add_all(ps); db_session.flush()
    for i,(dia,pid,cid) in enumerate([(date(2026,1,1),0,0),(date(2026,1,11),0,1),(date(2026,1,21),0,0),(date(2026,10,1),1,1)]):
        v=Venda(cliente_id=cs[cid].id,fabrica_id=fs[pid].id,data_venda=dia,numero_pedido=str(i),valor_total=20)
        db_session.add(v);db_session.flush()
        db_session.add(ItemVenda(venda_id=v.id,produto_id=ps[pid].id,quantidade=2,preco_unitario=10))
    db_session.commit()
    return cs,fs,ps


def cab(token):
    return {'Authorization': f'Bearer {token}'}


def test_fabrica_e_status_distintos_no_contrato_da_ficha(client, token_admin, carteira):
    cs,fs,ps=carteira
    ficha=client.get(f'/api/v1/clientes/{cs[0].id}',headers=cab(token_admin)).json()
    abandonado=ficha['produtos_em_abandono'][0]
    assert abandonado['fabrica']=='Fábrica EV' and abandonado['sku']=='21053'
    situacoes={f['fabrica']: f for f in ficha['resumo_fabricas']}
    assert situacoes['Fábrica EV']['situacao_atividade']=='Inativa'
    assert situacoes['Outra fábrica']['situacao_atividade']=='Ativa'
    assert 'situacao_recompra' in situacoes['Outra fábrica']
    produto=client.get('/api/v1/comercial/painel?mes=2026-10',headers=cab(token_admin)).json()['produtos'][0]
    assert produto['fabrica']=='Outra fábrica' and produto['sku']=='21053'


def test_atraso_no_ciclo_nao_torna_fabrica_inativa(db_session,carteira):
    from types import SimpleNamespace
    registros=[SimpleNamespace(fabrica_id=1,fabrica_nome='EV',venda_id=i,data_venda=REF-timedelta(days=d)) for i,d in enumerate([40,30,20])]
    fabrica=ClienteService(db_session)._analisar_fabricas(registros,REF)[0]
    assert fabrica['situacao_atividade']=='Ativa'
    assert fabrica['situacao_recompra']=='Recompra atrasada há 10 dias'


def test_acompanhamento_compartilhado_historico_e_concorrencia(client,token_admin,db_session,carteira):
    cs,fs,ps=carteira; h=cab(token_admin)
    grupo=client.get('/api/v1/comercial/alertas',headers=h).json()['itens'][0]
    assert grupo['resumo']['FABRICA_INATIVA']==1
    entrada={'situacao':'AGUARDANDO_RETORNO','motivo':'Cliente contatado','proximo_contato':'2026-10-20',
             'versao':0,'assinatura':grupo['assinatura']}
    salvo=client.post(f'/api/v1/comercial/alertas/{cs[1].id}/acompanhamento',json=entrada,headers=h)
    assert salvo.status_code==200,salvo.text
    assert salvo.json()['usuario']=='Admin Tester'
    assert client.post(f'/api/v1/comercial/alertas/{cs[0].id}/acompanhamento',json=entrada,headers=h).status_code==409
    lista=client.get(f'/api/v1/comercial/alertas?fabrica_id={fs[0].id}&situacao=AGUARDANDO_RETORNO',headers=h).json()
    assert lista['total']==1 and lista['itens'][0]['assinatura']==grupo['assinatura']
    assert client.get('/api/v1/comercial/alertas?situacao=DISPENSADO',headers=h).json()['total']==0
    entrada.update(situacao='DISPENSADO',motivo='Sem interesse neste momento',proximo_contato=None,versao=salvo.json()['versao'])
    assert client.post(f'/api/v1/comercial/alertas/{cs[0].id}/acompanhamento',json=entrada,headers=h).status_code==200
    hist=client.get(f'/api/v1/comercial/alertas/{cs[1].id}/historico',headers=h).json()
    assert [a['situacao'] for a in hist]==['DISPENSADO','AGUARDANDO_RETORNO']
    assert db_session.query(AcaoAlerta).count()==2


@pytest.mark.parametrize('alteracao',[
    {'situacao':'DISPENSADO','motivo':' '},
    {'situacao':'AGUARDANDO_RETORNO'},
    {'situacao':'CONTATADO','proximo_contato':'2026-10-17'},
    {'situacao':'PENDENTE','proximo_contato':'2026-10-20'},
])
def test_validacao_das_acoes(client,token_admin,carteira,alteracao):
    cs,_,_=carteira; h=cab(token_admin)
    grupo=client.get('/api/v1/comercial/alertas',headers=h).json()['itens'][0]
    r=client.post(f'/api/v1/comercial/alertas/{cs[0].id}/acompanhamento',json={'assinatura':grupo['assinatura'],**alteracao},headers=h)
    assert r.status_code==422


def test_novos_sinais_reabrem_acompanhamento_sem_apagar_eventos(client,token_admin,db_session,carteira):
    cs,fs,_=carteira; h=cab(token_admin)
    grupo=client.get('/api/v1/comercial/alertas',headers=h).json()['itens'][0]
    entrada={'situacao':'DISPENSADO','motivo':'Sem oportunidade','assinatura':grupo['assinatura']}
    assert client.post(f'/api/v1/comercial/alertas/{cs[0].id}/acompanhamento',json=entrada,headers=h).status_code==200
    db_session.add(Venda(cliente_id=cs[1].id,fabrica_id=fs[0].id,data_venda=date(2026,2,1),numero_pedido='novo-sinal',valor_total=10));db_session.commit()
    grupo=client.get('/api/v1/comercial/alertas?situacao=PENDENTE',headers=h).json()['itens'][0]
    assert grupo['acompanhamento']['novos_sinais'] is True
    assert grupo['acompanhamento']['situacao']=='PENDENTE'
    assert db_session.query(AcaoAlerta).count()==1


def test_acoes_autenticadas_e_assinatura_obsoleta(client,token_admin,carteira):
    cs,_,_=carteira
    caminho=f'/api/v1/comercial/alertas/{cs[0].id}'
    assert client.get(caminho+'/historico').status_code==401
    entrada={'situacao':'CONTATADO','assinatura':'0'*64}
    assert client.post(caminho+'/acompanhamento',json=entrada).status_code==401
    assert client.post(caminho+'/acompanhamento',json=entrada,headers=cab(token_admin)).status_code==409


def test_historico_disponivel_informa_periodo_e_ultima_carga(client,token_admin,db_session,carteira):
    cs,fs,_=carteira
    db_session.add(Importacao(arquivo='pedidos.xlsx',arquivo_itens='itens.xlsx',usuario='admin@teste.com',processados=4,criado_em=datetime(2026,10,18,12)))
    db_session.add(Venda(cliente_id=cs[0].id,fabrica_id=fs[0].id,data_venda=date(2099,1,1),numero_pedido='futuro',valor_total=10));db_session.commit()
    assert client.get('/api/v1/comercial/historico-disponivel').status_code==401
    h=client.get('/api/v1/comercial/historico-disponivel',headers=cab(token_admin)).json()
    assert h['inicio']=='2026-01-01' and h['fim']=='2026-10-01' and h['pedidos']==4
    assert h['ultima_importacao']['pedidos']==4
