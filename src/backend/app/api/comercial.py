from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from src.backend.app.api.deps import get_db, get_usuario_atual
from src.backend.app.models import Vendedor, Cliente, Fabrica, Venda
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
def alertas(vendedor_id: Optional[int] = None, tipo: Optional[str] = None, fabrica_id: Optional[int] = None,
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
    inicio = (pagina - 1) * limite
    return {"total": len(registros), "total_alertas": quantidade, "itens": registros[inicio:inicio + limite]}


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
