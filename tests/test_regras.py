from datetime import date, timedelta
import pytest
from src.backend.app.models import Cliente,Fabrica,Produto,Venda,ItemVenda,RegraNegocio,Usuario,Vendedor
from src.backend.app.core.security import criar_token_acesso,gerar_hash_senha
from src.backend.app.services.regras_service import MotorRegras
from src.backend.app.services.analise_service import AnaliseService
from src.backend.app.services.cliente_service import ClienteService
from src.backend.app.services.comercial_service import ComercialService
from src.backend.app.services.colaborativo_service import ColaborativoService

REF=date(2026,10,13)


@pytest.fixture
def base_regras(db_session):
    db=db_session
    fs=[Fabrica(nome_fantasia=n) for n in ['Fábrica principal','Outra fábrica']]
    cs=[Cliente(razao_social=n,grupo_economico=g,estado=uf) for n,g,uf in
        [('Fiscal PR','Rede PR','PR'),('Segundo PR','Rede PR','PR'),('Fiscal SC','Rede SC','SC')]]
    db.add_all(fs+cs);db.flush()
    ps=[Produto(fabrica_id=fs[0].id,sku=c,nome='Produto '+c) for c in ['21001','21053','21099']]
    ps.append(Produto(fabrica_id=fs[1].id,sku='21001',nome='Outra fábrica mesmo código'))
    db.add_all(ps);db.flush()
    def comprar(c,p,d,valor=10):
        v=Venda(cliente_id=cs[c].id,fabrica_id=ps[p].fabrica_id,numero_pedido=f'{c}-{p}-{d}',data_venda=date.fromisoformat(d),valor_total=valor)
        db.add(v);db.flush();db.add(ItemVenda(venda_id=v.id,produto_id=ps[p].id,quantidade=1,preco_unitario=valor));db.flush()
    for d in ['2026-01-01','2026-01-11']:comprar(0,0,d)
    comprar(1,1,'2026-01-21');comprar(2,0,'2026-01-01');comprar(2,1,'2026-01-11');comprar(2,2,'2026-01-21')
    db.commit()
    return fs,cs,ps,comprar


def substituicao(db,h,**kwargs):
    fs,cs,ps,_=h
    r=RegraNegocio(tipo='SUBSTITUICAO',fabrica_id=fs[0].id,produto_origem_id=ps[0].id,produto_destino_id=ps[1].id,inicio=date(2026,1,1),**kwargs)
    db.add(r);db.commit();return r


def test_substituicao_unifica_datas_ciclo_e_sucessor_sem_alterar_vendas(db_session,base_regras):
    h=base_regras;fs,cs,ps,_=h
    substituicao(db_session,h)
    ficha=ClienteService(db_session).obter_dossie_cliente(cs[0].id,ref_date=REF)
    assert len(ficha['produtos_em_abandono'])==1
    assert ficha['produtos_em_abandono'][0]['sku']=='21053'
    assert ficha['produtos_em_abandono'][0]['total_vezes_comprado']==3
    pos=AnaliseService(db_session,date(2026,9,29),REF).produtos_posicao(REF)
    assert pos[(cs[0].id,ps[1].id)]['datas']==3 and (cs[0].id,ps[0].id) not in pos
    assert db_session.query(ItemVenda).filter(ItemVenda.produto_id==ps[0].id).count()==3
    produtos=ColaborativoService(db_session).recomendar_produtos_cliente(cs[0].id)
    assert {r['sku'] for r in produtos}=={'21099'}


def test_compra_sucessor_interrompe_falso_abandono_e_alerta_do_codigo_antigo(db_session,base_regras):
    fs,cs,ps,comprar=base_regras
    substituicao(db_session,base_regras)
    comprar(1,1,'2026-10-12');db_session.commit()
    ficha=ClienteService(db_session).obter_dossie_cliente(cs[0].id,ref_date=REF)
    assert ficha['produtos_em_abandono']==[]
    alertas=ComercialService(db_session).alertas()
    assert not [a for a in alertas if a['cliente_id']==cs[0].id and a['tipo']=='PRODUTO_EM_RISCO']


def test_restricao_uf_nao_gera_inatividade_nem_sugestao_mantem_financeiro(db_session,base_regras):
    fs,cs,ps,_=base_regras
    db_session.add(RegraNegocio(tipo='RESTRICAO',fabrica_id=fs[0].id,uf='PR',inicio=date(2026,1,1)));db_session.commit()
    ficha=ClienteService(db_session).obter_dossie_cliente(cs[0].id,ref_date=REF)
    assert ficha['valor_comprado']==30 and ficha['resumo_fabricas']==[]
    assert ficha['sugestoes_expansao_mix']==[] and ficha['produtos_em_abandono']==[]
    assert not [a for a in ComercialService(db_session).alertas() if a['cliente_id']==cs[0].id]
    assert [a for a in ComercialService(db_session).alertas() if a['cliente_id']==cs[2].id]
    mapa=AnaliseService(db_session,date(2026,9,29),REF).relatorio('mapa')['linhas']
    assert {r['cliente'] for r in mapa}=={'Rede SC'}
    assert ComercialService(db_session).painel('2026-01')['indicadores']['venda_total']==60
    regioes=AnaliseService(db_session,date(2026,1,1),date(2026,1,31)).relatorio('regioes')['linhas']
    assert sum(r['atual'] for r in regioes)==60


def test_escopo_cliente_vigencia_fabricas_e_rede_com_ufs_distintas(db_session,base_regras):
    fs,cs,ps,_=base_regras
    r=substituicao(db_session,base_regras,cliente_id=cs[0].id)
    r.inicio=date(2026,10,1)
    cs[1].estado='SC'
    db_session.add(RegraNegocio(tipo='RESTRICAO',fabrica_id=fs[0].id,uf='PR',inicio=date(2026,10,1)))
    db_session.commit();m=MotorRegras(db_session)
    assert m.produto(ps[0].id,cs[1].id,REF)==ps[1].id
    assert m.produto(ps[0].id,cs[2].id,REF)==ps[0].id
    assert m.produto(ps[0].id,cs[0].id,date(2026,9,30))==ps[0].id
    assert m.produto(ps[3].id,cs[0].id,REF)==ps[3].id
    assert not m.bloqueada(cs[0].id,fs[0].id,REF)  # Rede ainda pode comprar no SC.
    assert m.bloqueada(cs[0].id,fs[0].id,REF,consolidar=False)
    assert not m.bloqueada(cs[0].id,fs[0].id,date(2026,9,30),consolidar=False)


def test_api_regras_permissoes_edicao_desativacao_e_validacoes(client,token_admin,db_session,base_regras):
    fs,cs,ps,_=base_regras
    h={'Authorization':f'Bearer {token_admin}'}
    dados={'tipo':'SUBSTITUICAO','fabrica_id':fs[0].id,'codigo_antigo':'21001','codigo_novo':'21053','inicio':'2026-01-01'}
    assert client.get('/api/v1/regras').status_code==401
    r=client.post('/api/v1/regras',json=dados,headers=h)
    assert r.status_code==200,r.text
    regra=r.json()
    assert regra['criado_por'] is not None
    assert client.post('/api/v1/regras',json=dados,headers=h).status_code==422
    ciclo={**dados,'codigo_antigo':'21053','codigo_novo':'21001'}
    assert client.post('/api/v1/regras',json=ciclo,headers=h).status_code==422
    assert client.post('/api/v1/regras',json={**dados,'codigo_novo':'inexistente'},headers=h).status_code==422
    assert client.post('/api/v1/regras',json={**dados,'fim':'2025-01-01'},headers=h).status_code==422
    r=client.post('/api/v1/regras/'+str(regra['id']),json={**dados,'ativa':False},headers=h)
    assert r.status_code==200 and r.json()['ativa'] is False
    assert MotorRegras(db_session).produto(ps[0].id,cs[0].id,REF)==ps[0].id
    u=Usuario(nome='Vendedor',email='vendedor-regras@example.com',senha_hash=gerar_hash_senha('teste12345'),perfil='vendedor',aprovado=True)
    db_session.add(u);db_session.commit()
    vendedor={'Authorization':'Bearer '+criar_token_acesso({'sub':u.email})}
    assert client.get('/api/v1/regras',headers=vendedor).status_code==200
    assert client.post('/api/v1/regras',json=dados,headers=vendedor).status_code==403


def test_ciclo_especifico_do_cliente_e_restricao_invalida_sao_rejeitados(client,token_admin,base_regras):
    fs,cs,ps,_=base_regras
    h={'Authorization':f'Bearer {token_admin}'}
    dados={'tipo':'SUBSTITUICAO','fabrica_id':fs[0].id,'codigo_antigo':'21001','codigo_novo':'21053','inicio':'2026-01-01'}
    assert client.post('/api/v1/regras',json=dados,headers=h).status_code==200
    assert client.post('/api/v1/regras',json={**dados,'cliente_id':cs[0].id,'codigo_antigo':'21053','codigo_novo':'21001'},headers=h).status_code==422
    assert client.post('/api/v1/regras',json={'tipo':'RESTRICAO','fabrica_id':fs[0].id,'uf':'XX'},headers=h).status_code==422


def test_excecao_usa_ultimo_vendedor_global_e_cliente_libera_a_rede(db_session,base_regras):
    fs,cs,ps,comprar=base_regras
    sergio,rodrigo=Vendedor(nome='Sergio teste'),Vendedor(nome='Rodrigo teste')
    db_session.add_all([sergio,rodrigo]);db_session.flush()
    for v in db_session.query(Venda):
        v.vendedor_id=sergio.id if v.cliente_id in [cs[0].id,cs[1].id] else rodrigo.id
    comprar(0,3,'2026-09-01')
    db_session.query(Venda).filter(Venda.fabrica_id==fs[1].id).one().vendedor_id=rodrigo.id
    cs[2].estado='PR'
    r=RegraNegocio(tipo='RESTRICAO',fabrica_id=fs[0].id,uf='PR',inicio=date(2026,1,1),excecoes_vendedores=[sergio.id])
    db_session.add(r);db_session.commit()
    m=MotorRegras(db_session)
    assert m.vendedor(cs[0].id,fs[0].id,REF)==rodrigo.id
    assert m.bloqueada(cs[1].id,fs[0].id,REF)
    assert m.bloqueada(cs[2].id,fs[0].id,REF)
    alertas=ComercialService(db_session).alertas()
    assert not any(a['cliente_id']==cs[0].id and a['fabrica_id']==fs[0].id for a in alertas)
    assert not any(a['cliente_id']==cs[2].id and a['fabrica_id']==fs[0].id for a in alertas)
    r.excecoes_clientes=[cs[2].id];db_session.commit()
    assert not MotorRegras(db_session).bloqueada(cs[2].id,fs[0].id,REF)
    db_session.add(RegraNegocio(tipo='RESTRICAO',fabrica_id=fs[0].id,cliente_id=cs[0].id,inicio=date(2026,1,1)))
    db_session.commit()
    assert MotorRegras(db_session).bloqueada(cs[0].id,fs[0].id,REF)  # Exceção não cancela outra regra.


def test_excecao_sergio_em_outra_fabrica_libera_cibra_so_durante_vigencia(db_session,base_regras):
    fs,cs,ps,comprar=base_regras
    fs[0].nome_fantasia='Cibra'
    sergio=Vendedor(nome='Sérgio');db_session.add(sergio);db_session.flush()
    comprar(1,3,'2026-06-30')
    ultima=db_session.query(Venda).order_by(Venda.data_venda.desc(),Venda.id.desc()).first()
    ultima.vendedor_id=sergio.id
    r=RegraNegocio(tipo='RESTRICAO',fabrica_id=fs[0].id,uf='PR',inicio=date(2026,7,1),fim=date(2026,9,30))
    db_session.add(r);db_session.commit()
    m=MotorRegras(db_session)
    assert not m.bloqueada(cs[0].id,fs[0].id,date(2026,6,30))
    assert m.bloqueada(cs[0].id,fs[0].id,date(2026,7,1))
    assert m.bloqueada(cs[0].id,fs[0].id,date(2026,9,30))
    assert not m.bloqueada(cs[0].id,fs[0].id,date(2026,10,1))
    r.excecoes_vendedores=[sergio.id];db_session.commit()
    m=MotorRegras(db_session)
    assert m.vendedor(cs[0].id,fs[0].id,REF)==sergio.id
    assert not m.bloqueada(cs[0].id,fs[0].id,date(2026,7,1))
    assert not m.bloqueada(cs[0].id,fs[0].id,date(2026,7,1),consolidar=False)
    assert ClienteService(db_session).obter_dossie_cliente(cs[0].id,ref_date=date(2026,7,1))['resumo_fabricas']
    assert ColaborativoService(db_session).recomendar_produtos_cliente(cs[0].id,ref_date=date(2026,7,1))
    assert sum(v.valor_total for v in db_session.query(Venda).filter(Venda.cliente_id.in_([cs[0].id,cs[1].id])))==40


@pytest.mark.parametrize('unificar',[True,False])
def test_substituicao_opcional_respeita_compra_e_referencia_sem_alterar_financeiro(db_session,base_regras,unificar):
    fs,cs,ps,comprar=base_regras
    r=substituicao(db_session,base_regras,unificar_historico=unificar)
    r.inicio=date(2026,7,1);db_session.commit()
    comprar(1,0,'2026-07-01');db_session.commit()
    motor=MotorRegras(db_session)
    assert motor.produto(ps[0].id,cs[0].id,date(2026,6,30))==ps[0].id
    assert motor.produto(ps[0].id,cs[0].id,REF,date(2026,1,1))==(ps[1].id if unificar else ps[0].id)
    assert motor.produto(ps[0].id,cs[0].id,REF,date(2026,7,1))==ps[1].id
    pos=AnaliseService(db_session,date(2026,7,1),REF).produtos_posicao(REF)
    assert pos[(cs[0].id,ps[1].id)]['datas']==(4 if unificar else 2)
    assert ((cs[0].id,ps[0].id) in pos) is (not unificar)
    ficha=ClienteService(db_session).obter_dossie_cliente(cs[0].id,ref_date=REF)
    assert ficha['valor_comprado']==40
    sugestoes=ColaborativoService(db_session).recomendar_produtos_cliente(cs[0].id,ref_date=REF)
    assert not {ps[0].id,ps[1].id} & {p['produto_id'] for p in sugestoes}
    assert db_session.query(ItemVenda).filter(ItemVenda.produto_id==ps[0].id).count()==4


def test_pedido_sem_itens_na_rede_sinaliza_incerteza_ate_recompra_conhecida(db_session,base_regras,monkeypatch,client,token_admin):
    fs,cs,ps,comprar=base_regras
    cs[0].grupo_economico='Depecil';cs[1].grupo_economico='  DEPECIL  '
    comprar(0,0,'2026-01-21')
    db_session.add(Venda(cliente_id=cs[1].id,fabrica_id=fs[0].id,numero_pedido='EV-sem-itens',data_venda=date(2026,10,12),valor_total=150))
    db_session.commit()
    monkeypatch.setattr('src.backend.app.services.comercial_service.hoje_comercial',lambda:REF)
    ficha=ClienteService(db_session).obter_dossie_cliente(cs[0].id,ref_date=REF)
    assert ficha['valor_comprado']==190 and ficha['clientes_agrupados']==2
    assert ficha['produtos_em_abandono']==[]
    assert {p['sku'] for p in ficha['produtos_sem_confirmacao']}=={'21001','21053'}
    assert all('não confirmada' in p['mensagem'] for p in ficha['produtos_sem_confirmacao'])
    resposta=client.get(f'/api/v1/clientes/{cs[0].id}',headers={'Authorization':f'Bearer {token_admin}'})
    assert resposta.status_code==200
    assert {p['sku'] for p in resposta.json()['produtos_sem_confirmacao']}=={'21001','21053'}
    assert not [a for a in ComercialService(db_session).alertas() if a['cliente_id']==cs[0].id and a['tipo']=='PRODUTO_EM_RISCO']
    assert AnaliseService(db_session,date(2026,9,29),REF).posicao(REF,{cs[0].id})['itens_sem_confirmacao']==2
    comprar(0,0,'2026-10-13');db_session.commit()
    ficha=ClienteService(db_session).obter_dossie_cliente(cs[0].id,ref_date=REF)
    assert {p['sku'] for p in ficha['produtos_sem_confirmacao']}=={'21053'}


def test_api_persiste_opcao_de_historico_anterior(client,token_admin,base_regras):
    fs,cs,ps,_=base_regras
    h={'Authorization':f'Bearer {token_admin}'}
    dados={'tipo':'SUBSTITUICAO','fabrica_id':fs[0].id,'codigo_antigo':'21001',
           'codigo_novo':'21053','inicio':'2026-07-01','unificar_historico':False}
    r=client.post('/api/v1/regras',json=dados,headers=h)
    assert r.status_code==200,r.text
    assert r.json()['unificar_historico'] is False
    assert client.get('/api/v1/regras',headers=h).json()['itens'][0]['unificar_historico'] is False


def test_mesma_rede_nao_e_vizinha_e_compra_futura_nao_entra_no_perfil(db_session,base_regras):
    fs,cs,ps,comprar=base_regras
    cs[0].grupo_economico='Rede   Depecil';cs[1].grupo_economico=' REDE depecil '
    futuro=Produto(fabrica_id=fs[0].id,sku='FUTURO',nome='Produto futuro');db_session.add(futuro);db_session.flush()
    v=Venda(cliente_id=cs[2].id,fabrica_id=fs[0].id,numero_pedido='futuro',data_venda=date(2099,1,1),valor_total=10)
    db_session.add(v);db_session.flush();db_session.add(ItemVenda(venda_id=v.id,produto_id=futuro.id,quantidade=1,preco_unitario=10));db_session.commit()
    s=ColaborativoService(db_session)
    perfis=s._carregar_perfis_consumo(REF)
    assert len(perfis)==2 and perfis['rede:rede depecil'][ps[1].id]==1
    assert all(futuro.id not in p for p in perfis.values())
    assert len(s.encontrar_grupos_similares(cs[0].id,ref_date=REF))==1
    assert {r['produto_id'] for r in s.recomendar_produtos_cliente(cs[0].id,ref_date=REF)}=={ps[2].id}
    assert s.recomendar_produtos_cliente(cs[0].id,ref_date=date(2025,12,31))==[]


def test_api_excecoes_normaliza_clientes_valida_vendedores_e_lista_nomes(client,token_admin,db_session,base_regras):
    fs,cs,ps,_=base_regras
    v=Vendedor(nome='Sergio teste');db_session.add(v);db_session.commit()
    h={'Authorization':f'Bearer {token_admin}'}
    dados={'tipo':'RESTRICAO','fabrica_id':fs[0].id,'uf':'PR','excecoes_clientes':[cs[1].id], 'excecoes_vendedores':[v.id]}
    r=client.post('/api/v1/regras',json=dados,headers=h)
    assert r.status_code==200,r.text
    assert r.json()['excecoes_clientes']==[cs[0].id]
    assert r.json()['excecoes_vendedores_detalhes']==[{'id':v.id,'nome':'Sergio teste'}]
    lista=client.get('/api/v1/regras',headers=h).json()['itens']
    assert lista[0]['excecoes_clientes_detalhes']==[{'id':cs[0].id,'nome':'Rede PR'}]
    assert client.post('/api/v1/regras',json={**dados,'excecoes_vendedores':[99999]},headers=h).status_code==422
    assert client.post('/api/v1/regras',json={**dados,'excecoes_clientes':[99999]},headers=h).status_code==422
