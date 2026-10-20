from datetime import date,timedelta
import pytest
from src.backend.app.models import Cliente,Fabrica,Produto,Venda,ItemVenda,Vendedor
from src.backend.app.services.analise_service import AnaliseService,hoje_comercial

BASE=date(2026,9,29)
FIM=date(2026,10,13)


def test_cnpjs_da_mesma_rede_nao_viram_novos_clientes_ou_falsos_inativos(db_session,historico):
    from src.backend.app.services.comercial_service import ComercialService
    from src.backend.app.services.cliente_service import ClienteService
    cs=historico['clientes']
    cs[0].grupo_economico=cs[2].grupo_economico='Cliente comercial A'
    db_session.commit()
    s=AnaliseService(db_session,BASE,FIM)
    d=s.comparativo(BASE)
    assert d['novos_clientes']==0
    assert d['antes']['clientes_total']==3
    assert d['depois']['clientes_reativados']==2
    mapa=s.relatorio('mapa')['linhas']
    assert len([r for r in mapa if r['cliente']=='Cliente comercial A'])==2
    precos=s.relatorio('precos')['linhas']
    novo_cnpj=next(r for r in precos if r['preco']==50)
    assert novo_cnpj['cliente']=='Cliente comercial A' and novo_cnpj['anterior']==12
    painel=ComercialService(db_session).painel('2026-10')
    assert painel['indicadores']['clientes_atendidos']==3
    assert painel['indicadores']['clientes_novos']==0
    assert len([r for r in painel['clientes'] if r['nome']=='Cliente comercial A'])==1
    ficha=ClienteService(db_session).obter_dossie_cliente(cs[0].id,ref_date=FIM)
    assert ficha['clientes_agrupados']==2 and len(ficha['cadastros_fiscais'])==2
    fiscal=ClienteService(db_session).obter_dossie_cliente(cs[2].id,ref_date=FIM,agrupar_rede=False)
    assert fiscal['valor_comprado']==50 and fiscal['clientes_agrupados']==1


def test_ciclo_de_produto_combina_datas_distintas_dos_cnpjs(db_session,historico):
    cs=historico['clientes']
    cs[0].grupo_economico=cs[3].grupo_economico='Rede unificada'
    db_session.commit()
    s=AnaliseService(db_session,BASE,FIM)
    produtos=s.produtos_posicao(BASE-timedelta(days=1))
    assert len(produtos)==2  # 3 datas iguais nos dois CNPJs contam uma vez.
    produto=next(r for chave,r in produtos.items() if chave[0]==cs[0].id)
    assert produto['datas']==3
    d=s.comparativo(BASE)
    assert d['antes']['clientes_inativos']==1
    assert d['depois']['itens_sem_confirmacao']==1  # Pedido sem itens de outro CNPJ.


def test_central_e_lista_exibem_uma_rede_apesar_de_cnpj_antigo_inativo(client,token_admin,db_session):
    from src.backend.app.services.comercial_service import ComercialService
    from datetime import timedelta
    f=Fabrica(nome_fantasia='Fábrica única')
    cs=[Cliente(razao_social='Cadastro '+str(i),grupo_economico='Rede ativa') for i in range(2)]
    db_session.add_all([f]+cs);db_session.flush()
    for i,dias in enumerate([120,2]):
        db_session.add(Venda(numero_pedido=str(i),cliente_id=cs[i].id,fabrica_id=f.id,data_venda=date.today()-timedelta(days=dias),valor_total=10))
    db_session.commit()
    assert ComercialService(db_session).alertas()==[]
    h={'Authorization':f'Bearer {token_admin}'}
    lista=client.get('/api/v1/comercial/clientes',headers=h).json()
    assert lista['total']==1 and lista['itens'][0]['cadastros_fiscais']==2
    ficha=client.get(f'/api/v1/clientes/{cs[1].id}',headers=h).json()
    assert ficha['clientes_agrupados']==2 and ficha['razao_social']=='Rede ativa'

@pytest.fixture
def historico(db_session):
    db=db_session
    fs=[Fabrica(nome_fantasia='Fábrica '+str(i)) for i in range(2)]
    vs=[Vendedor(nome='Vendedor '+str(i)) for i in range(2)]
    cs=[Cliente(razao_social=n,grupo_economico=None,micro_regiao=r,estado='SC') for n,r in [('Recuperado','Região A'),('Ativo','Região B'),('Novo','Região A'),('Sem confirmação',None)]]
    db.add_all(fs+vs+cs);db.flush()
    ps=[Produto(sku='SKU-1',nome='Produto '+str(i),fabrica_id=f.id) for i,f in enumerate(fs)]
    db.add_all(ps);db.flush()
    numero=[0]
    def venda(c,f,data,valor=10,item=True,vendedor=0):
        numero[0]+=1
        v=Venda(numero_pedido=str(numero[0]),cliente_id=cs[c].id,fabrica_id=fs[f].id,vendedor_id=vs[vendedor].id,data_venda=date.fromisoformat(data),valor_total=valor)
        db.add(v);db.flush()
        if item:db.add(ItemVenda(venda_id=v.id,produto_id=ps[f].id,quantidade=1,preco_unitario=valor))
        db.flush()
        return v
    for c in [0,3]:
        venda(c,0,'2026-01-01',8);venda(c,0,'2026-01-11',9);venda(c,0,'2026-01-21',10)
    venda(1,1,'2026-09-20',100)
    venda(0,0,'2026-10-01',12)
    venda(0,1,'2026-10-10',25)
    venda(1,1,'2026-10-05',20)
    venda(1,1,'2026-10-06',1000,vendedor=1)
    venda(2,0,'2026-10-02',50)
    venda(3,0,'2026-10-03',30,item=False)
    venda(0,0,'2026-10-20',999)
    db.commit()
    return {'fabricas':fs,'clientes':cs,'vendedores':vs,'venda':venda}


def test_comparativo_sem_vazamento_futuro_com_coorte_fixa(db_session,historico):
    d=AnaliseService(db_session,BASE,FIM).comparativo(BASE)
    assert d['base']=='2026-09-28' and d['dias_periodo']==15
    assert d['periodo_antes']=={'inicio':'2026-09-14','fim':'2026-09-28'}
    assert d['antes']['clientes_total']==d['depois']['clientes_total']==3
    assert d['antes']['clientes_inativos']==2 and d['depois']['clientes_inativos']==0
    assert d['antes']['itens_inativos']==2 and d['depois']['itens_inativos']==0
    assert d['depois']['itens_sem_confirmacao']==1
    assert d['antes']['itens_total']==d['depois']['itens_total']==3
    assert d['depois']['clientes_reativados']==2 and d['antes']['clientes_reativados']==0
    assert d['inativos_iniciais_recuperados']==2 and d['novos_clientes']==1
    assert d['criterio_itens']=='ciclo' and d['historico_90_dias']


def test_carteira_vendedor_inicial_nao_muda_com_transferencia(db_session,historico):
    d=AnaliseService(db_session,BASE,FIM,vendedor_id=historico['vendedores'][0].id).comparativo(BASE)
    assert d['antes']['clientes_total']==d['depois']['clientes_total']==3
    assert d['depois']['clientes_inativos']==0


def test_mapa_fabrica_mostra_cliente_que_nunca_comprou_nela(db_session,historico):
    h=historico
    d=AnaliseService(db_session,BASE,FIM,fabrica_id=h['fabricas'][0].id).relatorio('mapa',status='Sem compra')
    assert any(r['cliente']=='Ativo' for r in d['linhas'])
    assert all(r['status']=='Sem compra' and r['ultima'] is None for r in d['linhas'])


def test_mapa_padrao_somente_relacoes_com_compra_sem_excluir_inativas(db_session,historico):
    s=AnaliseService(db_session,BASE,FIM)
    padrao=s.relatorio('mapa')
    completo=s.relatorio('mapa',incluir_sem_compra=True)
    assert padrao['total']==5 and completo['total']==8
    assert all(r['ultima'] is not None and r['status']!='Sem compra' for r in padrao['linhas'])
    historico_anterior=AnaliseService(db_session,date(2026,9,1),date(2026,9,28)).relatorio('mapa')
    assert len([r for r in historico_anterior['linhas'] if r['status']=='Inativo'])==2


def test_inatividade_historica_nao_usa_compras_posteriores(db_session,historico):
    d=AnaliseService(db_session,date(2026,9,1),date(2026,9,28)).relatorio('inativos')
    assert {r['cliente'] for r in d['linhas']}=={'Recuperado','Sem confirmação'}
    assert all(r['dias']>=90 for r in d['linhas'])
    assert 'Novo' not in {r['cliente'] for r in d['linhas']}


def test_preco_anterior_fora_do_periodo_mesmo_cliente_e_fabrica(db_session,historico):
    d=AnaliseService(db_session,BASE,FIM,fabrica_id=historico['fabricas'][0].id).relatorio('precos',codigo='SKU-1')
    r=next(r for r in d['linhas'] if r['cliente']=='Recuperado')
    assert r['preco']==12 and r['anterior']==10 and r['variacao']==20
    assert all(r['preco']!=999 for r in d['linhas'])
    novo=next(r for r in d['linhas'] if r['cliente']=='Novo')
    assert novo['anterior'] is None and novo['variacao'] is None


def test_regioes_compara_mesma_duracao_e_nao_inclui_desconhecidas_na_media(db_session,historico):
    d=AnaliseService(db_session,date(2026,10,1),FIM,vendedor_id=historico['vendedores'][0].id).relatorio('regioes')
    b=next(r for r in d['linhas'] if r['regiao']=='Região B')
    assert b['anterior']==100 and b['atual']==20 and b['variacao']==-80
    assert b['clientes']==1 and b['diferenca_media']==-.5
    desconhecida=next(r for r in d['linhas'] if r['regiao']=='Região não identificada')
    assert desconhecida['diferenca_media'] is None


def test_resultado_reativacao_cliente_diferente_de_fabrica(db_session,historico):
    s=AnaliseService(db_session,BASE,FIM)
    global_=next(r for r in s.relatorio('reativacoes')['linhas'] if r['cliente']=='Recuperado')
    fabrica=next(r for r in s.relatorio('reativacoes',escopo='fabrica')['linhas'] if r['cliente']=='Recuperado')
    assert global_['novos_pedidos']==1 and global_['valor_posterior']==37
    assert fabrica['novos_pedidos']==0 and fabrica['valor_posterior']==12
    assert global_['pedido_retorno']=='8' and global_['valor_retorno']==12
    assert global_['valor_apos_retorno']==25
    assert fabrica['valor_apos_retorno']==0
    colunas={c['chave']:c for c in s.relatorio('reativacoes')['colunas']}
    assert colunas['pedido_retorno']['formato']=='texto'
    assert colunas['novos_pedidos']['formato']=='numero'
    assert colunas['valor_apos_retorno']['formato']=='moeda'


def test_reativacoes_repetidas_nao_duplicam_faturamento(db_session,historico):
    f=historico['fabricas'][0]
    c=Cliente(razao_social='Reincidente',grupo_economico='Somente reincidente');db_session.add(c);db_session.flush()
    for i,(data,valor) in enumerate([('2026-01-01',20),('2026-04-05',100),('2026-05-01',50),('2026-07-31',200)]):
        db_session.add(Venda(numero_pedido='RE-'+str(i),cliente_id=c.id,fabrica_id=f.id,data_venda=date.fromisoformat(data),valor_total=valor))
    db_session.commit()
    d=AnaliseService(db_session,date(2026,4,1),FIM,rede='Somente reincidente').relatorio('reativacoes')
    assert len(d['linhas'])==2 and sum(r['valor_posterior'] for r in d['linhas'])==350


def test_api_analises_paginacao_pdf_e_periodos_invalidos(client,token_admin,historico):
    assert client.get('/api/v1/analises/impacto').status_code==401
    h={'Authorization':f'Bearer {token_admin}'}
    r=client.get('/api/v1/analises/impacto?implantacao=2026-09-29&fim=2026-10-13',headers=h)
    assert r.status_code==200,r.text
    assert client.get('/api/v1/analises/impacto?implantacao=2026-10-13&fim=2026-09-29',headers=h).status_code==422
    futuro=(hoje_comercial()+timedelta(days=1)).isoformat()
    assert client.get('/api/v1/analises/impacto?fim='+futuro,headers=h).status_code==422
    for tipo in ['mapa','reativacoes','inativos','precos','regioes']:
        url=f'/api/v1/analises/relatorios/{tipo}?inicio=2026-09-01&fim=2026-10-13'
        d=client.get(url+'&limite=1',headers=h)
        assert d.status_code==200,d.text
        assert len(d.json()['linhas'])<=1
        pdf=client.get(f'/api/v1/analises/relatorios/{tipo}/pdf?inicio=2026-09-01&fim=2026-10-13',headers=h)
        assert pdf.status_code==200,pdf.text if pdf.status_code!=200 else ''
        assert pdf.content.startswith(b'%PDF')
    assert client.get('/api/v1/analises/relatorios/inventado',headers=h).status_code==422
    mapa='/api/v1/analises/relatorios/mapa?inicio=2026-09-29&fim=2026-10-13'
    assert client.get(mapa,headers=h).json()['total']==5
    assert client.get(mapa+'&incluir_sem_compra=true',headers=h).json()['total']==8
