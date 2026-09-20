from datetime import date
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict


class ClienteBase(BaseModel):
    razao_social: str
    nome_fantasia: Optional[str] = None
    cnpj_cpf: Optional[str] = None
    grupo_economico: Optional[str] = None
    cidade: Optional[str] = None
    estado: Optional[str] = None


class ClienteOptionOut(ClienteBase):
    """Schema enxuto para autocomplete e listagem de busca."""
    id: int

    model_config = ConfigDict(from_attributes=True)


class FabricaResumoOut(BaseModel):
    fabrica_id: int
    fabrica: str
    ultima_compra: str
    dias_sem_comprar: int
    ciclo_medio_dias: int
    dias_para_vencer: int
    data_limite_inatividade: str
    status: str
    status_gatilho: str
    risco_bloqueio_neste_mes: bool


class ReposicaoOut(BaseModel):
    produto_id: int
    sku: str
    nome: str
    ciclo_medio: int
    dias_desde_ultima: int
    status: str
    volume_habitual: float


class AbandonoOut(BaseModel):
    produto_id: int
    sku: str
    nome: str
    dias_parado: int
    ciclo_habitual: int
    total_vezes_comprado: int


class YoYOut(BaseModel):
    periodo_recente: str
    periodo_comparado: str
    faturamento_recente: float
    faturamento_ano_anterior: float
    crescimento_pct: float


class RecomendacaoProdutoOut(BaseModel):
    produto_id: int
    sku: str
    nome: str
    score: Optional[float] = None


class ClienteDetalhesOut(BaseModel):
    """Dossiê Analítico 360 retornado pela rota GET /clientes/{id}/dossie."""
    cliente_id: int
    razao_social: str
    cnpj_cpf: Optional[str] = None
    micro_regiao: Optional[str] = None
    grupo_economico: Optional[str] = None
    mensagem: Optional[str] = None
    resumo_fabricas: List[FabricaResumoOut] = []
    sugestoes_reposicao: List[ReposicaoOut] = []
    produtos_em_abandono: List[AbandonoOut] = []
    performance_yoy: Optional[YoYOut] = None
    sugestoes_expansao_mix: List[RecomendacaoProdutoOut] = []

    model_config = ConfigDict(from_attributes=True)