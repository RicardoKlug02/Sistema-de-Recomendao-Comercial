from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List

from app.api.deps import get_db
from app.schemas.cliente import ClienteOptionOut, ClienteDetalhesOut
from app.services.cliente_service import ClienteService

router = APIRouter(prefix="/clientes", tags=["Clientes"])

# 1. Endpoint da barra de busca
@router.get("/busca", response_model=List[ClienteOptionOut])
def buscar_clientes(
    termo: str = Query(..., min_length=2, description="Razão Social ou CNPJ"),
    db: Session = Depends(get_db)
):
    service = ClienteService(db_session=db)
    return service.buscar_por_termo(termo)

# 2. Endpoint da ficha completa (carregado ao selecionar o resultado)
@router.get("/{cliente_id}", response_model=ClienteDetalhesOut)
def obter_ficha_cliente(cliente_id: int, db: Session = Depends(get_db)):
    service = ClienteService(db_session=db)
    detalhes = service.obter_detalhes_por_id(cliente_id)
    if not detalhes:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente não encontrado."
        )
    return detalhes