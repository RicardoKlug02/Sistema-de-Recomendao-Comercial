from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.backend.app.core.database import get_db
from src.backend.app.api.deps import get_usuario_atual
from src.backend.app.models.cliente_analises import (
    AlertaComercial,
    ClienteAnalytics,
    FabricaAnalytics,
    ResumoVendasGeral,
)
from src.backend.app.schemas.analytics_schemas import (
    AlertaComercialResponse,
    ClienteAnalyticsResponse,
    FabricaAnalyticsResponse,
    ResumoVendasGeralResponse,
)

router = APIRouter(prefix="/analytics", tags=["Analytics & Inteligência Comercial"], dependencies=[Depends(get_usuario_atual)])


@router.get("/resumo-vendas", response_model=List[ResumoVendasGeralResponse])
def listar_resumo_vendas(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Retorna o resumo consolidado de vendas por mês, região, vendedor e fábrica."""
    return db.query(ResumoVendasGeral).offset(skip).limit(limit).all()


@router.get("/cliente/{cliente_id}", response_model=ClienteAnalyticsResponse)
def obter_analytics_cliente(cliente_id: int, db: Session = Depends(get_db)):
    """Retorna o Raio-X completo 360º de um cliente específico."""
    analise = db.query(ClienteAnalytics).filter(ClienteAnalytics.cliente_id == cliente_id).first()
    if not analise:
        raise HTTPException(status_code=404, detail="Analytics não encontrado para este cliente.")
    return analise


@router.get("/fabricas", response_model=List[FabricaAnalyticsResponse])
def listar_fabrica_analytics(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Retorna os indicadores estratégicos consolidados por Fábrica e Região."""
    return db.query(FabricaAnalytics).offset(skip).limit(limit).all()


@router.get("/alertas", response_model=List[AlertaComercialResponse])
def listar_alertas_comerciais(tipo: Optional[str] = None, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Retorna os alertas comerciais gerados (ex: clientes inativos há mais de 90 dias)."""
    query = db.query(AlertaComercial)
    if tipo:
        query = query.filter(AlertaComercial.tipo_alerta == tipo)
    return query.offset(skip).limit(limit).all()
