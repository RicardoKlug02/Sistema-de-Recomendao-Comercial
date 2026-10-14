"""Políticas comerciais aplicadas à análise, sem reescrever as vendas fiscais."""
from collections import defaultdict
from types import SimpleNamespace
from sqlalchemy import case
from src.backend.app.models import RegraNegocio, Produto, ItemVenda, Venda
from src.backend.app.services.datas import hoje_comercial
from src.backend.app.services.identidade_cliente import IdentidadeCliente


class MotorRegras:
    def __init__(self, db, identidade=None, regras=None):
        self.identidade = identidade or IdentidadeCliente(db)
        self.regras = regras if regras is not None else db.query(RegraNegocio).filter(RegraNegocio.ativa.is_(True)).all()
        self.db = db
        self._mapas = {}
        self._bloqueios = {}
        self._produtos = None
        self._vendedores = {}

    @property
    def produtos(self):
        if self._produtos is None:
            self._produtos = {p.id:p for p in self.db.query(Produto.id,Produto.sku,Produto.nome,Produto.fabrica_id)}
        return self._produtos

    @staticmethod
    def vigente(r, ref):
        return r.ativa and r.inicio <= ref and (r.fim is None or ref <= r.fim)

    def aplica_cliente(self, r, cid):
        return r.cliente_id is None or (cid is not None and self.identidade.id(r.cliente_id) == self.identidade.id(cid))

    def mapa(self, cid=None, ref=None):
        ref = ref or hoje_comercial()
        chave = (self.identidade.id(cid) if cid is not None else None,ref)
        if chave not in self._mapas:
            regras = [r for r in self.regras if r.tipo=='SUBSTITUICAO' and self.vigente(r,ref) and self.aplica_cliente(r,cid)]
            # A substituição específica do cliente prevalece sobre a geral da fábrica.
            regras.sort(key=lambda r:r.cliente_id is not None)
            self._mapas[chave] = {r.produto_origem_id:r.produto_destino_id for r in regras}
        return self._mapas[chave]

    def produto(self, pid, cid=None, ref=None):
        mapa = self.mapa(cid,ref)
        vistos = set()
        while pid in mapa:
            if pid in vistos:
                raise ValueError('As substituições formam um ciclo. Revise os códigos de origem e destino.')
            vistos.add(pid)
            pid = mapa[pid]
        return pid

    def vendedor(self, cid, fid, ref, consolidar=True):
        chave=(ref,consolidar)
        if chave not in self._vendedores:
            por_fabrica,global_={},{}
            for v in (self.db.query(Venda.cliente_id,Venda.fabrica_id,Venda.vendedor_id)
                      .filter(Venda.data_venda<=ref).order_by(Venda.data_venda,Venda.id)):
                cliente=self.identidade.id(v.cliente_id) if consolidar else v.cliente_id
                por_fabrica[(cliente,v.fabrica_id)]=v.vendedor_id
                global_[cliente]=v.vendedor_id
            self._vendedores[chave]=(por_fabrica,global_)
        por_fabrica,global_=self._vendedores[chave]
        cliente=self.identidade.id(cid) if consolidar else cid
        return por_fabrica.get((cliente,fid),global_.get(cliente))

    def bloqueada(self, cid, fid, ref=None, consolidar=True):
        ref = ref or hoje_comercial()
        chave = (cid,fid,ref,consolidar)
        if chave not in self._bloqueios:
            fiscais = self.identidade.fiscais(cid) if consolidar else [cid]
            regras = [r for r in self.regras if r.tipo=='RESTRICAO' and r.fabrica_id==fid
                      and self.vigente(r,ref) and self.aplica_cliente(r,cid)]
            if regras:
                vendedor=self.vendedor(cid,fid,ref,consolidar)
                comercial=self.identidade.id(cid)
                regras=[r for r in regras if comercial not in {self.identidade.id(c) for c in (r.excecoes_clientes or [])}
                        and vendedor not in (r.excecoes_vendedores or [])]
            self._bloqueios[chave] = all(any(r.uf is None or r.uf == (self.identidade.clientes[fiscal].estado or '').strip().upper()
                                                    for r in regras) for fiscal in fiscais)
        return self._bloqueios[chave]

    def produto_sql(self, cliente_expr, ref):
        def expressao(cid):
            mapa = {pid:self.produto(pid,cid,ref) for pid in self.mapa(cid,ref)}
            return case(mapa,value=ItemVenda.produto_id,else_=ItemVenda.produto_id) if mapa else ItemVenda.produto_id
        geral = expressao(None)
        clientes = {self.identidade.id(r.cliente_id) for r in self.regras
                    if r.cliente_id is not None and r.tipo=='SUBSTITUICAO' and self.vigente(r,ref)}
        casos = [(cliente_expr.in_(self.identidade.fiscais(cid)),expressao(cid)) for cid in clientes]
        return case(*casos,else_=geral) if casos else geral

    def registros(self, registros, cid, ref, consolidar=True):
        resultado = []
        for r in registros:
            if self.bloqueada(cid,r.fabrica_id,ref,consolidar):
                continue
            dados = dict(r._mapping)
            if r.produto_id is not None:
                pid = self.produto(r.produto_id,cid,ref)
                if pid != r.produto_id:
                    p = self.produtos[pid]
                    dados.update(produto_id=pid,sku=p.sku,produto_nome=p.nome)
            resultado.append(SimpleNamespace(**dados))
        return resultado

    def perfil(self, perfil, cid=None, ref=None):
        novo = defaultdict(float)
        for pid,qtd in perfil.items():
            p = self.produtos[pid]
            if cid is None or not self.bloqueada(cid,p.fabrica_id,ref):
                novo[self.produto(pid,cid,ref)] += qtd
        return dict(novo)
