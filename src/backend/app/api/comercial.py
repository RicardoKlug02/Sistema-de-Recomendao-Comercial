from typing import Optional
from datetime import date
from typing import Literal
from pydantic import BaseModel, Field, model_validator
from sqlalchemy import func
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from src.backend.app.api.deps import get_db, get_usuario_atual
from src.backend.app.models import Vendedor, Cliente, Fabrica, Venda, Importacao, AcaoAlerta, Usuario
from src.backend.app.services.datas import hoje_comercial
from src.backend.app.services.acompanhamento_service import acompanhamentos, payload
from src.backend.app.services.comercial_service import ComercialService
from src.backend.app.services.cliente_service import ClienteService
from src.backend.app.services.identidade_cliente import IdentidadeCliente

router = APIRouter(prefix="/comercial", tags=["Painel e Central de Alertas"],
                   dependencies=[Depends(get_usuario_atual)])


@router.get("/painel")
def painel(mes: Optional[str] = Query(None, pattern=r"^\d{4}-(0[1-9]|1[0-2])$"),
           vendedor_id: Optional[int] = None, fabrica_id: Optional[int] = None, db: Session = Depends(get_db)):
    try:
        return ComercialService(db).painel(mes, vendedor_id, fabrica_id)
    except ValueError:
        raise HTTPException(422, "Mês inválido.")


@router.get("/vendedores")
def vendedores(db: Session = Depends(get_db)):
    return [{"id": v.id, "nome": v.nome} for v in db.query(Vendedor).order_by(Vendedor.nome).all()]


@router.get("/alertas")
def alertas(vendedor_id: Optional[int] = None, tipo: Optional[str] = None, fabrica_id: Optional[int] = None, situacao: Optional[Literal['PENDENTE','CONTATADO','AGUARDANDO_RETORNO','DISPENSADO']] = None,
            pagina: int = Query(1, ge=1), limite: int = Query(50, ge=1, le=200), db: Session = Depends(get_db)):
    registros = ComercialService(db).alertas(vendedor_id, fabrica_id)
    if tipo:
        registros = [r for r in registros if r["tipo"] == tipo]
    quantidade = len(registros)
    grupos = {}
    for r in registros:
        grupo = grupos.setdefault(r["cliente_id"], {"id": f"cliente:{r['cliente_id']}",
            "cliente_id": r["cliente_id"], "cliente": r["cliente"], "prioridade": r["prioridade"], "alertas": []})
        grupo["prioridade"] = min(grupo["prioridade"], r["prioridade"])
        grupo["alertas"].append(r)
    registros = list(grupos.values())
    estados = acompanhamentos(db,IdentidadeCliente(db))
    for grupo in registros:
        assinatura = grupo['alertas'][0]['assinatura']
        anterior = estados.get(grupo['cliente_id'])
        mudou = anterior is not None and anterior['assinatura'] != assinatura
        grupo['assinatura'] = assinatura
        grupo['acompanhamento'] = {**(anterior or {'versao':0,'situacao':'PENDENTE','motivo':'','proximo_contato':None}),
                                   'novos_sinais':mudou}
        if mudou:
            grupo['acompanhamento'].update(situacao='PENDENTE',motivo='',proximo_contato=None)
        grupo['resumo'] = {t:sum(a['tipo']==t for a in grupo['alertas']) for t in {a['tipo'] for a in grupo['alertas']}}
    if situacao:
        registros = [g for g in registros if g['acompanhamento']['situacao']==situacao]
    quantidade = sum(len(g['alertas']) for g in registros)
    inicio = (pagina - 1) * limite
    return {"total": len(registros), "total_alertas": quantidade, "itens": registros[inicio:inicio + limite]}


@router.get('/historico-disponivel')
def historico_disponivel(db:Session=Depends(get_db)):
    inicio,fim,pedidos = db.query(func.min(Venda.data_venda),func.max(Venda.data_venda),func.count(Venda.id)).filter(Venda.data_venda<=hoje_comercial()).one()
    ultima = db.query(Importacao).order_by(Importacao.id.desc()).first()
    return {'inicio':inicio,'fim':fim,'pedidos':pedidos,
            'ultima_importacao':{'data':ultima.criado_em,'pedidos':ultima.processados} if ultima else None}


class AcaoEntrada(BaseModel):
    situacao: Literal['PENDENTE','CONTATADO','AGUARDANDO_RETORNO','DISPENSADO']
    motivo: str = Field('',max_length=1000)
    proximo_contato: date | None = None
    versao: int = Field(0,ge=0)
    assinatura: str = Field(pattern=r'^[a-f0-9]{64}$')

    @model_validator(mode='after')
    def validar(self):
        self.motivo = self.motivo.strip()
        if self.situacao=='DISPENSADO' and not self.motivo:
            raise ValueError('Informe o motivo para dispensar o acompanhamento.')
        if self.situacao=='AGUARDANDO_RETORNO' and self.proximo_contato is None:
            raise ValueError('Informe a próxima data de contato.')
        if self.situacao in ('PENDENTE','DISPENSADO') and self.proximo_contato is not None:
            raise ValueError('Use uma próxima data apenas para Contatado ou Aguardando retorno.')
        if self.proximo_contato is not None and self.proximo_contato<hoje_comercial():
            raise ValueError('A próxima data de contato deve ser hoje ou uma data futura.')
        return self


@router.post('/alertas/{cliente_id}/acompanhamento')
def salvar_acompanhamento(cliente_id:int, entrada:AcaoEntrada, db:Session=Depends(get_db),usuario:Usuario=Depends(get_usuario_atual)):
    identidade=IdentidadeCliente(db)
    if cliente_id not in identidade.clientes:
        raise HTTPException(404,'Cliente não encontrado.')
    cid=identidade.id(cliente_id)
    db.query(Cliente).filter(Cliente.id==cid).with_for_update().one()
    anterior=acompanhamentos(db,identidade).get(cid)
    if entrada.versao != (anterior['versao'] if anterior else 0):
        raise HTTPException(409,'Outro usuário atualizou este acompanhamento. Atualize a lista antes de salvar.')
    sinais=[a for a in ComercialService(db).alertas() if a['cliente_id']==cid]
    if not sinais or sinais[0]['assinatura']!=entrada.assinatura:
        raise HTTPException(409,'Os sinais mudaram. Atualize a lista e revise o acompanhamento.')
    acao=AcaoAlerta(cliente_id=cid,usuario_id=usuario.id,**entrada.model_dump(exclude={'versao'}))
    db.add(acao);db.commit();db.refresh(acao)
    return payload(acao,usuario.nome)


@router.get('/alertas/{cliente_id}/historico')
def historico_alerta(cliente_id:int, db:Session=Depends(get_db)):
    identidade=IdentidadeCliente(db)
    if cliente_id not in identidade.clientes:
        raise HTTPException(404,'Cliente não encontrado.')
    return [payload(a,nome) for a,nome in db.query(AcaoAlerta,Usuario.nome).join(Usuario,Usuario.id==AcaoAlerta.usuario_id)
            .filter(AcaoAlerta.cliente_id.in_(identidade.fiscais(cliente_id))).order_by(AcaoAlerta.id.desc()).limit(30)]


@router.get("/fabricas")
def fabricas(db: Session = Depends(get_db)):
    return [{"id": f.id, "nome": f.nome_fantasia} for f in db.query(Fabrica.id, Fabrica.nome_fantasia).order_by(Fabrica.nome_fantasia)]


@router.get("/clientes")
def clientes(termo: str = "", pagina: int = Query(1, ge=1), limite: int = Query(30, ge=1, le=100),
             fabrica_id: Optional[int] = None, db: Session = Depends(get_db)):
    inicio = (pagina - 1) * limite
    identidade = IdentidadeCliente(db)
    if termo.strip():
        encontrados = ClienteService(db).buscar_por_termo(termo, limite=None)
        ids = {identidade.id(c['id']) for c in encontrados}
    else:
        query = db.query(Cliente.id)
        if fabrica_id is not None:
            query = query.filter(db.query(Venda.id).filter(Venda.cliente_id == Cliente.id, Venda.fabrica_id == fabrica_id).exists())
        ids = {identidade.id(c.id) for c in query}
    if fabrica_id is not None:
        compradores = {identidade.id(v.cliente_id) for v in db.query(Venda.cliente_id).filter(Venda.fabrica_id == fabrica_id).distinct()}
        ids &= compradores
    escolhidos = sorted(ids)[inicio:inicio + limite]
    fiscais = {c.id: c for c in db.query(Cliente).filter(Cliente.id.in_(escolhidos))}
    return {"total": len(ids), "itens": [{"id": cid, "razao_social": identidade.nome(cid),
            "cidade": fiscais[cid].cidade, "estado": fiscais[cid].estado,
            "grupo_economico": fiscais[cid].grupo_economico,
            "cadastros_fiscais": len(identidade.fiscais(cid))} for cid in escolhidos]}
