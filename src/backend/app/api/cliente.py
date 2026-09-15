from typing import Any, Dict, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from src.backend.app.api.deps import get_db, get_usuario_atual
from src.backend.app.models.usuario import Usuario
from src.backend.app.schemas.cliente import ClienteOptionOut, ClienteDetalhesOut
from src.backend.app.services.associacao_service import AssociacaoService
from src.backend.app.services.cliente_service import ClienteService
from src.backend.app.services.recompra_service import RecompraService

router = APIRouter(prefix="/clientes", tags=["Clientes"])


@router.get("/busca", response_model=List[ClienteOptionOut])
def buscar_clientes(
    termo: str = Query(..., min_length=2, description="Razão Social, Nome Fantasia ou CNPJ/CPF"),
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_usuario_atual),
):
    """Autocomplete rápido para a barra de busca global do React."""
    service = ClienteService(db_session=db)
    return service.buscar_por_termo(termo)


@router.get("/alertas/home", response_model=List[Dict[str, Any]])
def obter_alertas_dashboard(
    limite: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_usuario_atual),
):
    """Carrega os cards da tela inicial com os clientes em risco crítico de churn."""
    service = RecompraService(db_session=db)
    return service.obter_alertas_globais_alto_volume(limite_alertas=limite)


@router.post("/cross-selling", response_model=List[Dict[str, Any]])
def obter_cross_selling(
    produtos_ids: List[int],
    top_n: int = Query(4, ge=1, le=10),
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_usuario_atual),
):
    """Sugestão instantânea de venda casada para itens incluídos em cotações/carrinhos."""
    service = AssociacaoService(db_session=db)
    return service.recomendar_cross_selling(produto_ids=produtos_ids, top_n=top_n)


@router.get("/{cliente_id}", response_model=ClienteDetalhesOut)
def obter_ficha_cliente(
    cliente_id: int,
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_usuario_atual),
):
    """Dossiê 360 do cliente: faturamento recente, ciclo por fábrica, reposições e abandono."""
    service = ClienteService(db_session=db)
    detalhes = service.obter_dossie_cliente(cliente_id)

    if not detalhes:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente não localizado na base.",
        )

    return detalhes