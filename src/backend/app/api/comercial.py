from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from src.backend.app.api.deps import get_db, get_usuario_atual
from src.backend.app.models import Vendedor, Cliente
from src.backend.app.services.comercial_service import ComercialService
from src.backend.app.services.cliente_service import ClienteService

router = APIRouter(prefix="/comercial", tags=["Painel e Central de Alertas"],
                   dependencies=[Depends(get_usuario_atual)])


@router.get("/painel")
def painel(mes: Optional[str] = Query(None, pattern=r"^\d{4}-(0[1-9]|1[0-2])$"),
           vendedor_id: Optional[int] = None, db: Session = Depends(get_db)):
    try:
        return ComercialService(db).painel(mes, vendedor_id)
    except ValueError:
        raise HTTPException(422, "Mês inválido.")


@router.get("/vendedores")
def vendedores(db: Session = Depends(get_db)):
    return [{"id": v.id, "nome": v.nome} for v in db.query(Vendedor).order_by(Vendedor.nome).all()]


@router.get("/alertas")
def alertas(vendedor_id: Optional[int] = None, tipo: Optional[str] = None,
            pagina: int = Query(1, ge=1), limite: int = Query(50, ge=1, le=200), db: Session = Depends(get_db)):
    registros = ComercialService(db).alertas(vendedor_id)
    if tipo:
        registros = [r for r in registros if r["tipo"] == tipo]
    inicio = (pagina - 1) * limite
    return {"total": len(registros), "itens": registros[inicio:inicio + limite]}


@router.get("/clientes")
def clientes(termo: str = "", pagina: int = Query(1, ge=1), limite: int = Query(30, ge=1, le=100),
             db: Session = Depends(get_db)):
    inicio = (pagina - 1) * limite
    if termo.strip():
        registros = ClienteService(db).buscar_por_termo(termo, limite=10000)
        return {"total": len(registros), "itens": registros[inicio:inicio + limite]}
    query = db.query(Cliente).order_by(Cliente.id)
    return {"total": query.count(), "itens": [{"id": c.id, "razao_social": c.razao_social,
            "cidade": c.cidade, "estado": c.estado, "grupo_economico": c.grupo_economico}
            for c in query.offset(inicio).limit(limite).all()]}
