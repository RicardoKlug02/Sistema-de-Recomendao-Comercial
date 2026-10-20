from datetime import date
from typing import Optional
from pydantic import BaseModel, ConfigDict


class ResumoVendasGeralResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ano_mes: str
    regiao_imediata: str
    vendedor_id: Optional[int] = None
    fabrica_id: Optional[int] = None
    total_vendas: float
    quantidade_pedidos: int
    ticket_medio: float


class ClienteAnalyticsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    cliente_id: int
    venda_ultimo_mes: float
    media_ultimos_6_meses: float
    crescimento_percentual: float
    top_fabricas_json: Optional[str] = None
    sugestoes_fabricas_json: Optional[str] = None
    produtos_recomendados_json: Optional[str] = None
    produtos_parados_json: Optional[str] = None
    produtos_risco_inatividade_json: Optional[str] = None
    produtos_sem_segunda_compra_json: Optional[str] = None


class FabricaAnalyticsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    fabrica_id: int
    regiao_imediata: str
    total_vendas: float
    volume_vendido: float
    tendencia_venda: Optional[str] = None
    top_produtos_json: Optional[str] = None


class AlertaComercialResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tipo_alerta: str
    cliente_id: Optional[int] = None
    vendedor_id: Optional[int] = None
    fabrica_id: Optional[int] = None
    descricao_acao: Optional[str] = None
    data_referencia: Optional[date] = None