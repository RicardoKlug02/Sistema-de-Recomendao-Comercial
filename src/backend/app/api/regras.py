from datetime import date, timedelta
from types import SimpleNamespace
from typing import Literal
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field, model_validator
from sqlalchemy import func, text
from sqlalchemy.orm import Session
from src.backend.app.api.deps import get_db, get_usuario_atual, get_usuario_admin
from src.backend.app.models import RegraNegocio, Fabrica, Produto, Vendedor
from src.backend.app.services.regras_service import MotorRegras
from src.backend.app.services.datas import hoje_comercial

router = APIRouter(prefix='/regras',tags=['Regras de negócio'],dependencies=[Depends(get_usuario_atual)])
UFS = set('AC AL AP AM BA CE DF ES GO MA MT MS MG PA PB PR PE PI RJ RN RS RO RR SC SP SE TO'.split())


class RegraEntrada(BaseModel):
    model_config = ConfigDict(extra='forbid')
    tipo: Literal['SUBSTITUICAO','RESTRICAO']
    fabrica_id: int = Field(gt=0)
    cliente_id: int | None = Field(None,gt=0)
    uf: str | None = None
    codigo_antigo: str | None = Field(None,max_length=150)
    codigo_novo: str | None = Field(None,max_length=150)
    excecoes_clientes: list[int] = Field(default_factory=list,max_length=500)
    excecoes_vendedores: list[int] = Field(default_factory=list,max_length=500)
    inicio: date = Field(default_factory=hoje_comercial)
    fim: date | None = None
    ativa: bool = True
    motivo: str = Field('',max_length=1000)

    @model_validator(mode='after')
    def validar(self):
        self.uf = (self.uf or '').strip().upper() or None
        self.codigo_antigo = (self.codigo_antigo or '').strip() or None
        self.codigo_novo = (self.codigo_novo or '').strip() or None
        if self.fim is not None and self.fim < self.inicio:
            raise ValueError('A data final deve ser igual ou posterior ao início da vigência.')
        if self.uf and self.uf not in UFS:
            raise ValueError('Selecione uma UF válida.')
        if self.tipo=='SUBSTITUICAO' and (self.excecoes_clientes or self.excecoes_vendedores):
            raise ValueError('Exceções de clientes ou vendedores são usadas nas restrições de venda.')
        if self.tipo=='SUBSTITUICAO':
            if not self.codigo_antigo or not self.codigo_novo or self.uf:
                raise ValueError('Informe código antigo e novo da mesma fábrica. Substituições não usam filtro por UF.')
        elif self.codigo_antigo or self.codigo_novo:
            raise ValueError('Restrições de fábrica não devem informar códigos de produtos.')
        return self


def travar(db):
    if db.bind.dialect.name=='postgresql':
        db.execute(text('SELECT pg_advisory_xact_lock(20261013, 1)'))


def validar_regras(db, regras):
    ativas=[r for r in regras if r.ativa]
    motor=MotorRegras(db,regras=ativas)
    substituicoes=[r for r in ativas if r.tipo=='SUBSTITUICAO']
    for i,a in enumerate(substituicoes):
        for b in substituicoes[i+1:]:
            mesmo_cliente=(a.cliente_id is None and b.cliente_id is None) or (a.cliente_id is not None and b.cliente_id is not None and motor.identidade.id(a.cliente_id)==motor.identidade.id(b.cliente_id))
            sobrepoe=max(a.inicio,b.inicio)<=min(a.fim or date.max,b.fim or date.max)
            if mesmo_cliente and a.produto_origem_id==b.produto_origem_id and sobrepoe:
                raise ValueError('Já existe substituição desse código no mesmo escopo e vigência. Edite ou encerre a regra existente.')
    datas={r.inicio for r in substituicoes}
    datas|={r.fim+timedelta(days=1) for r in substituicoes if r.fim is not None and r.fim<date.max}
    clientes={None}|{r.cliente_id for r in substituicoes if r.cliente_id is not None}
    for ref in datas:
        for cid in clientes:
            for pid in motor.mapa(cid,ref):
                motor.produto(pid,cid,ref)


def preparar(db,entrada):
    if db.get(Fabrica,entrada.fabrica_id) is None:
        raise ValueError('Fábrica não encontrada.')
    identidade=MotorRegras(db,regras=[]).identidade
    if entrada.cliente_id is not None and entrada.cliente_id not in identidade.clientes:
        raise ValueError('Cliente não encontrado.')
    if any(cid not in identidade.clientes for cid in entrada.excecoes_clientes):
        raise ValueError('Um dos clientes com exceção não foi encontrado.')
    vendedores={v.id for v in db.query(Vendedor.id).filter(Vendedor.id.in_(entrada.excecoes_vendedores))}
    if vendedores != set(entrada.excecoes_vendedores):
        raise ValueError('Um dos vendedores com exceção não foi encontrado.')
    dados={k:v for k,v in entrada.model_dump().items() if k not in ('codigo_antigo','codigo_novo')}
    dados['excecoes_clientes']=sorted({identidade.id(cid) for cid in entrada.excecoes_clientes})
    dados['excecoes_vendedores']=sorted(set(entrada.excecoes_vendedores))
    if entrada.cliente_id is not None:
        dados['cliente_id']=identidade.id(entrada.cliente_id)
    dados.update(produto_origem_id=None,produto_destino_id=None)
    if entrada.tipo=='SUBSTITUICAO':
        for campo,codigo in [('produto_origem_id',entrada.codigo_antigo),('produto_destino_id',entrada.codigo_novo)]:
            produtos=db.query(Produto.id).filter(Produto.fabrica_id==entrada.fabrica_id,func.lower(Produto.sku)==codigo.lower()).all()
            if len(produtos)!=1:
                raise ValueError(f'Código {codigo} não encontrado de forma única nesta fábrica. Importe o produto antes de cadastrar a regra.')
            dados[campo]=produtos[0].id
        if dados['produto_origem_id']==dados['produto_destino_id']:
            raise ValueError('O código novo deve ser diferente do antigo.')
    return dados


def saida(db,r):
    f=db.get(Fabrica,r.fabrica_id)
    motor=MotorRegras(db,regras=[])
    antigo=db.get(Produto,r.produto_origem_id) if r.produto_origem_id else None
    novo=db.get(Produto,r.produto_destino_id) if r.produto_destino_id else None
    return {**{c.name:getattr(r,c.name) for c in RegraNegocio.__table__.columns},
            'fabrica':f.nome_fantasia,'cliente':motor.identidade.nome(r.cliente_id) if r.cliente_id else None,
            'codigo_antigo':antigo.sku if antigo else None,'codigo_novo':novo.sku if novo else None,
            **detalhes_excecoes(r,motor,{v.id:v.nome for v in db.query(Vendedor.id,Vendedor.nome)})}


def detalhes_excecoes(r,motor,vendedores):
    return {'excecoes_clientes_detalhes':[{'id':cid,'nome':motor.identidade.nome(cid)} for cid in (r.excecoes_clientes or [])],
            'excecoes_vendedores_detalhes':[{'id':vid,'nome':vendedores.get(vid,'Vendedor não encontrado')} for vid in (r.excecoes_vendedores or [])]}


@router.get('')
def listar(pagina:int=Query(1,ge=1),limite:int=Query(30,ge=1,le=100),db:Session=Depends(get_db)):
    q=db.query(RegraNegocio).order_by(RegraNegocio.id.desc())
    # Os catálogos são carregados uma vez para a página inteira.
    motor=MotorRegras(db,regras=[])
    vendedores={v.id:v.nome for v in db.query(Vendedor.id,Vendedor.nome)}
    fabricas={f.id:f.nome_fantasia for f in db.query(Fabrica.id,Fabrica.nome_fantasia)}
    linhas=[]
    for r in q.offset((pagina-1)*limite).limit(limite):
        linhas.append({**{c.name:getattr(r,c.name) for c in RegraNegocio.__table__.columns},
            'fabrica':fabricas[r.fabrica_id], 'cliente':motor.identidade.nome(r.cliente_id) if r.cliente_id else None,
            'codigo_antigo':motor.produtos[r.produto_origem_id].sku if r.produto_origem_id else None,
            'codigo_novo':motor.produtos[r.produto_destino_id].sku if r.produto_destino_id else None,
            **detalhes_excecoes(r,motor,vendedores)})
    return {'total':q.count(),'itens':linhas}


@router.post('')
def criar(entrada:RegraEntrada,db:Session=Depends(get_db),usuario=Depends(get_usuario_admin)):
    try:
        travar(db)
        dados=preparar(db,entrada)
        candidato=SimpleNamespace(**dados)
        validar_regras(db,db.query(RegraNegocio).all()+[candidato])
        r=RegraNegocio(**dados,criado_por=usuario.id,atualizado_por=usuario.id)
        db.add(r);db.commit();db.refresh(r)
        return saida(db,r)
    except ValueError as e:
        db.rollback()
        raise HTTPException(422,str(e))


@router.post('/{regra_id}')
def editar(regra_id:int,entrada:RegraEntrada,db:Session=Depends(get_db),usuario=Depends(get_usuario_admin)):
    try:
        travar(db)
        r=db.get(RegraNegocio,regra_id)
        if r is None:raise HTTPException(404,'Regra não encontrada.')
        dados=preparar(db,entrada)
        validar_regras(db,db.query(RegraNegocio).filter(RegraNegocio.id!=regra_id).all()+[SimpleNamespace(**dados)])
        for k,v in dados.items():setattr(r,k,v)
        r.atualizado_por=usuario.id
        db.commit();db.refresh(r)
        return saida(db,r)
    except ValueError as e:
        db.rollback()
        raise HTTPException(422,str(e))
