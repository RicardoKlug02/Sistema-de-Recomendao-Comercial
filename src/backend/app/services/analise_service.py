"""Relatórios temporais calculados a partir das vendas efetivamente importadas."""
from collections import defaultdict
from types import SimpleNamespace
from datetime import date, timedelta
from src.backend.app.services.datas import hoje_comercial
from sqlalchemy import func
from src.backend.app.services.identidade_cliente import IdentidadeCliente
from src.backend.app.models import Cliente, Fabrica, Venda, Produto, ItemVenda, Vendedor


def variacao(atual, anterior):
    return round((atual / anterior - 1) * 100, 2) if anterior else None


class AnaliseService:
    def __init__(self, db, inicio, fim, vendedor_id=None, fabrica_id=None, rede=None):
        if inicio > fim or fim > hoje_comercial() or inicio.toordinal() <= (fim-inicio).days+1:
            raise ValueError('Informe um período válido, com data final até hoje.')
        self.db, self.inicio, self.fim = db, inicio, fim
        self.vendedor_id, self.fabrica_id, self.rede = vendedor_id, fabrica_id, rede
        self.identidade = IdentidadeCliente(db)
        self.rede_ids = [cid for cid,c in self.identidade.clientes.items()
                         if (c.grupo_economico or '').strip().casefold() == (rede or '').strip().casefold()]
        q = db.query(Venda.id, Venda.cliente_id, Venda.fabrica_id, Venda.vendedor_id, Venda.data_venda, Venda.valor_total).filter(Venda.data_venda <= fim)
        if rede:
            q = q.filter(Venda.cliente_id.in_(self.rede_ids))
        registros = q.order_by(Venda.data_venda, Venda.id).all()
        self.fiscal_por_venda = {v.id: v.cliente_id for v in registros}
        self.vendas = [SimpleNamespace(**{**v._mapping, "cliente_id": self.identidade.id(v.cliente_id)})
                       for v in registros]
        self._clientes = None
        self._produtos_cache = {}
        self.fabricas = {f.id: f.nome_fantasia for f in db.query(Fabrica.id, Fabrica.nome_fantasia)}
        self.vendedores = {v.id: v.nome for v in db.query(Vendedor.id, Vendedor.nome)}

    @property
    def clientes(self):
        if self._clientes is None:
            ids = {v.cliente_id for v in self.vendas}
            self._clientes = {cid: self.identidade.clientes[cid] for cid in ids}
        return self._clientes

    def escopo(self, referencia=None):
        return [v for v in self.vendas if (referencia is None or v.data_venda <= referencia)
                and (self.fabrica_id is None or v.fabrica_id == self.fabrica_id)]

    def ultimos(self, referencia):
        return {v.cliente_id: v for v in self.escopo(referencia)}

    def carteira(self, referencia):
        return {cid for cid, v in self.ultimos(referencia).items()
                if self.vendedor_id is None or v.vendedor_id == self.vendedor_id}

    def eventos(self, escopo='cliente', carteira=None):
        grupos = defaultdict(list)
        for v in self.vendas:
            chave = (v.cliente_id, v.fabrica_id) if escopo == 'fabrica' else v.cliente_id
            grupos[chave].append(v)
        resultado = []
        for historico in grupos.values():
            retornos = [i for i in range(1, len(historico)) if (historico[i].data_venda - historico[i-1].data_venda).days >= 90]
            for pos, indice in enumerate(retornos):
                v, anterior = historico[indice], historico[indice-1]
                if carteira is not None and v.cliente_id not in carteira:
                    continue
                if self.fabrica_id is not None and v.fabrica_id != self.fabrica_id:
                    continue
                if carteira is None and self.vendedor_id is not None and v.vendedor_id != self.vendedor_id:
                    continue
                limite = retornos[pos+1] if pos+1 < len(retornos) else len(historico)
                episodio = historico[indice:limite]
                resultado.append({'venda': v, 'anterior': anterior, 'episodio': episodio})
        return resultado

    def produtos_posicao(self, referencia):
        if referencia in self._produtos_cache:
            return self._produtos_cache[referencia]
        # Materializa a identidade em subconsulta: PostgreSQL com parâmetros posicionais
        # não reconhece CASE repetido no SELECT/GROUP BY como a mesma expressão.
        q = (self.db.query(self.identidade.expressao().label('comercial_id'),
             ItemVenda.produto_id, Venda.fabrica_id, Venda.data_venda)
             .join(ItemVenda, ItemVenda.venda_id == Venda.id).filter(Venda.data_venda <= referencia))
        if self.fabrica_id is not None:
            q = q.filter(Venda.fabrica_id == self.fabrica_id)
        if self.rede:
            q = q.filter(Venda.cliente_id.in_(self.rede_ids))
        base = q.subquery()
        registros = (self.db.query(base.c.comercial_id, base.c.produto_id, base.c.fabrica_id,
                     func.min(base.c.data_venda), func.max(base.c.data_venda),
                     func.count(func.distinct(base.c.data_venda)))
                     .group_by(base.c.comercial_id, base.c.produto_id, base.c.fabrica_id))
        resultado = {(r[0],r[1]): {'fabrica_id':r[2], 'primeira':r[3], 'ultima':r[4], 'datas':r[5]}
                     for r in registros}
        self._produtos_cache[referencia] = resultado
        return resultado

    def posicao(self, referencia, carteira, pares=None, produtos=None, criterio='ciclo'):
        vendas = [v for v in self.escopo(referencia) if v.cliente_id in carteira]
        ultimos = {v.cliente_id:v for v in vendas}
        relacoes = {(v.cliente_id,v.fabrica_id):v for v in vendas}
        inativos = {cid for cid,v in ultimos.items() if (referencia-v.data_venda).days >= 90}
        sem_itens_ids = {r[0] for r in self.db.query(Venda.id).filter(Venda.id.in_([v.id for v in vendas]), ~Venda.itens.any())}
        desconhecidos = {}
        for v in vendas:
            if v.id in sem_itens_ids:
                desconhecidos[(v.cliente_id,v.fabrica_id)] = v.data_venda
        conhecidos = self.produtos_posicao(referencia)
        pool = produtos if produtos is not None else {p for p in conhecidos if p[0] in carteira}
        itens_inativos = itens_incerto = 0
        for chave in pool:
            r = conhecidos.get(chave)
            if not r:
                continue
            if desconhecidos.get((chave[0],r['fabrica_id']), date.min) > r['ultima']:
                itens_incerto += 1
                continue
            dias = (referencia-r['ultima']).days
            if criterio == 'ciclo':
                ciclo = int((r['ultima']-r['primeira']).days/(r['datas']-1)) if r['datas'] >= 3 else None
                itens_inativos += ciclo is not None and dias >= 60 and dias > ciclo*2.5
            else:
                itens_inativos += dias >= 90
        universo_pares = pares if pares is not None else set(relacoes)
        return {'clientes_total':len(carteira), 'clientes_inativos':len(inativos),
                'taxa_inatividade':round(len(inativos)/len(carteira)*100,2) if carteira else None,
                'relacoes_inativas':sum((referencia-relacoes[p].data_venda).days >= 90 for p in universo_pares if p in relacoes),
                'itens_inativos':int(itens_inativos), 'itens_sem_confirmacao':itens_incerto,
                'itens_total':len(pool), 'pedidos_sem_itens':len(sem_itens_ids), 'inativos_ids':inativos}

    def comparativo(self, implantacao, criterio='ciclo'):
        base = implantacao-timedelta(days=1)
        dias = (self.fim-implantacao).days+1
        inicio_antes = implantacao-timedelta(days=dias)
        carteira = self.carteira(base)
        antes_vendas = [v for v in self.escopo(base) if v.cliente_id in carteira]
        pares = {(v.cliente_id,v.fabrica_id) for v in antes_vendas}
        produtos = {p for p in self.produtos_posicao(base) if p[0] in carteira}
        antes = self.posicao(base,carteira,pares,produtos,criterio)
        depois = self.posicao(self.fim,carteira,pares,produtos,criterio)
        eventos = self.eventos('fabrica' if self.fabrica_id is not None else 'cliente',carteira)
        retornos_antes = {r['venda'].cliente_id for r in eventos if inicio_antes <= r['venda'].data_venda <= base}
        retornos_depois = {r['venda'].cliente_id for r in eventos if implantacao <= r['venda'].data_venda <= self.fim}
        antes['clientes_reativados'], depois['clientes_reativados'] = len(retornos_antes), len(retornos_depois)
        compraram_depois = {v.cliente_id for v in self.escopo() if implantacao <= v.data_venda <= self.fim}
        recuperados = antes.pop('inativos_ids') & compraram_depois
        depois.pop('inativos_ids')
        novas_primeiras = {}
        for v in self.escopo(): novas_primeiras.setdefault(v.cliente_id,v)
        novos = sum(v.data_venda >= implantacao and (self.vendedor_id is None or v.vendedor_id == self.vendedor_id) for v in novas_primeiras.values())
        primeira = min((v.data_venda for v in self.escopo()),default=None)
        return {'implantacao':implantacao.isoformat(), 'base':base.isoformat(), 'fim':self.fim.isoformat(),
                'periodo_antes':{'inicio':inicio_antes.isoformat(),'fim':base.isoformat()},
                'periodo_depois':{'inicio':implantacao.isoformat(),'fim':self.fim.isoformat()}, 'dias_periodo':dias,
                'antes':antes,'depois':depois,'inativos_iniciais_recuperados':len(recuperados),
                'novos_clientes':novos,'historico_desde':primeira.isoformat() if primeira else None,
                'historico_90_dias':primeira is not None and primeira <= base-timedelta(days=90),
                'criterio_itens':criterio, 'escopo':'fábrica selecionada' if self.fabrica_id else 'escritório',
                'nota':'Cada rede conta como um cliente comercial; CNPJs sem rede contam individualmente. Comparativo observacional do histórico importado: não comprova causalidade do sistema. A carteira inicial permanece fixa; compras posteriores por outros vendedores também contam para sua atividade.'}

    def relatorio(self,tipo,status=None,codigo=None,escopo='cliente'):
        metodos = {'mapa':self.mapa,'reativacoes':lambda:self.reativacoes(escopo),
                   'inativos':self.inativos,'precos':lambda:self.precos(codigo),'regioes':self.regioes}
        if tipo not in metodos:
            raise ValueError('Relatório não encontrado.')
        dados = metodos[tipo]()
        if status and tipo == 'mapa': dados['linhas'] = [r for r in dados['linhas'] if r['status']==status]
        dados.update(tipo=tipo,total=len(dados['linhas']),inicio=self.inicio.isoformat(),fim=self.fim.isoformat(),
                     filtros={'fabrica':self.fabricas.get(self.fabrica_id,'Todas as fábricas'),
                              'vendedor':self.vendedores.get(self.vendedor_id,'Toda a equipe'),'rede':self.rede or 'Todas as redes'})
        return dados

    @staticmethod
    def tabela(titulo,colunas,linhas,notas):
        return {'titulo':titulo,'colunas':[{'chave':c[0],'titulo':c[1],'formato':c[2] if len(c)>2 else 'texto'} for c in colunas],
                'linhas':linhas,'notas':['Cada rede é um cliente comercial; CNPJs sem rede são individuais. Compras de todos os CNPJs da rede compõem seu histórico.'] + notas}

    def mapa(self):
        ultimo_global = {v.cliente_id:v for v in self.vendas}
        carteira = {cid for cid,v in ultimo_global.items() if self.vendedor_id is None or v.vendedor_id == self.vendedor_id}
        pares = {(v.cliente_id,v.fabrica_id):v for v in self.escopo()}
        fabricas = {self.fabrica_id:self.fabricas[self.fabrica_id]} if self.fabrica_id in self.fabricas else self.fabricas
        linhas=[]
        for cid in sorted(carteira):
            for fid,nome in fabricas.items():
                v=pares.get((cid,fid)); dias=(self.fim-v.data_venda).days if v else None
                linhas.append({'cliente':self.identidade.nome(cid),'rede':self.clientes[cid].grupo_economico or '—',
                    'fabrica':nome,'ultima':v.data_venda.isoformat() if v else None,'dias':dias,
                    'status':'Sem compra' if v is None else 'Inativo' if dias >= 90 else 'Ativo'})
        return self.tabela('Mapa cliente x fábrica',[('cliente','Cliente'),('rede','Rede'),('fabrica','Fábrica'),('ultima','Última compra','data'),('dias','Dias sem compra','numero'),('status','Situação')],linhas,
            ['Posição na data final. Ativo: última compra há menos de 90 dias; inativo: 90 dias ou mais; sem compra: nenhuma compra conhecida nesta fábrica.',
             'Carteira do vendedor conforme a última compra do cliente no escritório. Inclui as fábricas atualmente cadastradas.'])

    def inativos(self):
        linhas=[]
        ultimos=self.ultimos(self.fim)
        for cid in sorted(self.carteira(self.fim)):
            v=ultimos[cid]; dias=(self.fim-v.data_venda).days
            if dias < 90: continue
            c=self.clientes[cid]
            linhas.append({'cliente':self.identidade.nome(c.id),'rede':c.grupo_economico or '—','regiao':c.micro_regiao or 'Não identificada',
                'uf':c.estado or '—','ultima':v.data_venda.isoformat(),'dias':dias,'vendedor':self.vendedores.get(v.vendedor_id,'Não informado')})
        linhas.sort(key=lambda r:-r['dias'])
        return self.tabela('Clientes inativos',[('cliente','Cliente'),('rede','Rede'),('regiao','Região imediata'),('uf','UF'),('ultima','Última compra','data'),('dias','Dias sem compra','numero'),('vendedor','Último vendedor')],linhas,
            ['Posição na data final. Sem filtro de fábrica, considera compras em todo o escritório. Com fábrica selecionada, mostra inatividade nessa fábrica.',
             'Inatividade: pelo menos 90 dias. Clientes sem nenhuma compra conhecida não são classificados como inativos.'])

    def reativacoes(self,escopo):
        linhas=[]
        for r in self.eventos(escopo):
            v=r['venda']
            if not self.inicio <= v.data_venda <= self.fim: continue
            episodio=r['episodio']; c=self.clientes[v.cliente_id]
            linhas.append({'cliente':self.identidade.nome(c.id),'fabrica':self.fabricas[v.fabrica_id],'retorno':v.data_venda.isoformat(),
                'dias':(v.data_venda-r['anterior'].data_venda).days,'valor_retorno':v.valor_total,
                'valor_posterior':round(sum(e.valor_total for e in episodio),2),'novos_pedidos':len(episodio)-1,
                'acompanhamento':(self.fim-v.data_venda).days,'situacao':'Com novo pedido' if len(episodio)>1 else 'Sem novo pedido até a data final'})
        linhas.sort(key=lambda r:(r['retorno'],r['cliente']),reverse=True)
        return self.tabela('Resultado das reativações',[('cliente','Cliente'),('fabrica','Fábrica do retorno'),('retorno','Retorno','data'),('dias','Dias anteriores sem compra','numero'),('valor_retorno','Pedido de retorno','moeda'),('valor_posterior','Valor desde o retorno','moeda'),('novos_pedidos','Pedidos seguintes','numero'),('acompanhamento','Dias observados','numero'),('situacao','Resultado observado')],linhas,
            [('Reativação de cliente no escritório.' if escopo=='cliente' else 'Reativação da relação cliente x fábrica.'),
             'Retorno após pelo menos 90 dias sem compra. Primeiras compras não são reativações. O valor desde o retorno inclui o pedido de retorno e vai até a data final ou a próxima reativação, sem duplicar episódios.',
             'O vendedor é o do pedido de retorno; os pedidos seguintes podem ser de outros vendedores. Sem novo pedido não significa insucesso: observe o tempo de acompanhamento.'])

    def precos(self,codigo):
        q=(self.db.query(Venda.cliente_id,Venda.data_venda,Venda.id.label('venda_id'),Venda.numero_pedido,Venda.vendedor_id,
             Produto.sku,Produto.nome,Produto.fabrica_id,ItemVenda.preco_unitario,
             func.lag(ItemVenda.preco_unitario).over(partition_by=(self.identidade.expressao(),ItemVenda.produto_id),
             order_by=(Venda.data_venda,Venda.id,ItemVenda.id)).label('anterior'))
             .join(ItemVenda,ItemVenda.venda_id==Venda.id).join(Produto,Produto.id==ItemVenda.produto_id).filter(Venda.data_venda<=self.fim))
        if self.fabrica_id is not None:q=q.filter(Venda.fabrica_id==self.fabrica_id)
        if self.rede:q=q.filter(Venda.cliente_id.in_(self.rede_ids))
        if codigo:q=q.filter(Produto.sku==codigo.strip())
        janela=q.subquery()
        consulta=self.db.query(janela).filter(janela.c.data_venda>=self.inicio)
        if self.vendedor_id is not None:consulta=consulta.filter(janela.c.vendedor_id==self.vendedor_id)
        linhas=[{'cliente':self.identidade.nome(r.cliente_id),'codigo':r.sku+' · '+r.nome,
                 'fabrica':self.fabricas[r.fabrica_id],'data':r.data_venda.isoformat(),'pedido':r.numero_pedido,
                 'anterior':r.anterior,'preco':r.preco_unitario,'variacao':variacao(r.preco_unitario,r.anterior)}
                for r in consulta.order_by(janela.c.data_venda.desc(),janela.c.venda_id.desc())]
        return self.tabela('Evolução dos preços por código',[('cliente','Cliente'),('codigo','Código / produto'),('fabrica','Fábrica'),('data','Compra','data'),('pedido','Pedido'),('anterior','Preço anterior','moeda'),('preco','Preço unitário','moeda'),('variacao','Variação','percentual')],linhas,
            ['Compara o preço com a compra anterior do mesmo cliente e produto na mesma fábrica, inclusive quando a compra anterior é anterior ao período selecionado.',
             'Preço anterior ausente ou zero: variação sem base. Pedidos sem itens não informam preços. As variações não geram alertas automáticos.'])

    def regioes(self):
        dias=(self.fim-self.inicio).days+1; inicio_anterior=self.inicio-timedelta(days=dias)
        regioes={}
        for v in self.escopo():
            if self.vendedor_id is not None and v.vendedor_id!=self.vendedor_id:continue
            c=self.identidade.clientes[self.fiscal_por_venda[v.id]]; chave=(c.micro_regiao or 'Região não identificada',c.estado or 'UF não informada')
            r=regioes.setdefault(chave,{'regiao':chave[0],'uf':chave[1],'anterior':0,'atual':0,'clientes_antes':set(),'clientes_agora':set(),'identificada':bool(c.micro_regiao)})
            if self.inicio<=v.data_venda<=self.fim:r['atual']+=v.valor_total;r['clientes_agora'].add(v.cliente_id)
            elif inicio_anterior<=v.data_venda<self.inicio:r['anterior']+=v.valor_total;r['clientes_antes'].add(v.cliente_id)
        identificadas=[r for r in regioes.values() if r['identificada']]
        media=sum(len(r['clientes_agora']) for r in identificadas)/len(identificadas) if identificadas else None
        linhas=[]
        for r in regioes.values():
            n=len(r['clientes_agora'])
            linhas.append({'regiao':r['regiao'],'uf':r['uf'],'clientes_antes':len(r['clientes_antes']),'clientes':n,
                'anterior':round(r['anterior'],2),'atual':round(r['atual'],2),'variacao':variacao(r['atual'],r['anterior']),
                'diferenca_media':round(n-media,2) if r['identificada'] and media is not None else None})
        linhas.sort(key=lambda r:(r['clientes'],r['atual'],r['regiao']))
        return self.tabela('Regiões imediatas por vendedor',[('regiao','Região imediata'),('uf','UF'),('clientes_antes','Clientes antes','numero'),('clientes','Clientes no período','numero'),('anterior','Venda anterior','moeda'),('atual','Venda no período','moeda'),('variacao','Variação de venda','percentual'),('diferenca_media','Clientes em relação à média','numero')],linhas,
            [f'Período anterior de mesma duração: {inicio_anterior.isoformat()} até {(self.inicio-timedelta(days=1)).isoformat()}. Clientes são redes comerciais distintas (ou cadastros sem rede) atendidas em cada período.',
             'Diferença negativa para a média indica menos clientes atendidos que a média das regiões conhecidas deste vendedor; não mede potencial de mercado. Inclui regiões já presentes no histórico, mesmo sem vendas recentes.',
             'Região conforme cadastro fiscal atual da venda; uma rede presente em regiões diferentes conta uma vez em cada região, portanto os totais regionais de clientes não são somáveis. Regiões não identificadas aparecem separadamente e não entram na média. Quedas são informativas e não geram alertas automáticos.'])