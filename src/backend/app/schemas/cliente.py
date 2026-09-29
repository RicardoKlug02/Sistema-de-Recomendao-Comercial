import html
import re
from datetime import date
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


class SanitizedBaseModel(BaseModel):
    """Modelo base com remoção de espaços e escape contra XSS/Injeção."""
    model_config = ConfigDict(str_strip_whitespace=True, from_attributes=True)

    @field_validator("*", mode="before")
    @classmethod
    def sanitizar_strings(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip()
        return value


class ClienteBuscaParams(SanitizedBaseModel):
    """Validador estrito para parâmetros de pesquisa."""
    termo: str = Field(..., min_length=1, max_length=100)
    limite: int = Field(default=15, ge=1, le=100)

    @field_validator("termo")
    @classmethod
    def validar_termo(cls, v: str) -> str:
        # Bloqueia caracteres de controle suspeitos
        if not re.match(r"^[\w\s\.\-\/\,]+$", v, re.UNICODE):
            raise ValueError("O termo de busca contém caracteres inválidos.")
        return v


class ClienteBase(SanitizedBaseModel):
    razao_social: str = Field(..., min_length=1, max_length=255)
    nome_fantasia: Optional[str] = Field(None, max_length=255)
    cnpj_cpf: Optional[str] = Field(None, max_length=20)
    grupo_economico: Optional[str] = Field(None, max_length=150)
    cidade: Optional[str] = Field(None, max_length=100)
    estado: Optional[str] = Field(None, max_length=2)


class ClienteOptionOut(ClienteBase):
    id: int


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
    afinidade_percentual: Optional[float] = None
    classificacao: Optional[str] = None
    volume_sugerido_unidades: Optional[int] = None
    motivo: Optional[str] = None


class ClienteDetalhesOut(BaseModel):
    cliente_id: int
    razao_social: str
    cnpj_cpf: Optional[str] = None
    micro_regiao: Optional[str] = None
    grupo_economico: Optional[str] = None
    mensagem: Optional[str] = None
    valor_comprado: float = 0
    pedidos_emitidos: int = 0
    clientes_agrupados: int = 1
    sugestoes_fabricas: List[dict] = []
    resumo_fabricas: List[FabricaResumoOut] = []
    sugestoes_reposicao: List[ReposicaoOut] = []
    produtos_em_abandono: List[AbandonoOut] = []
    performance_yoy: Optional[YoYOut] = None
    sugestoes_expansao_mix: List[RecomendacaoProdutoOut] = []

    model_config = ConfigDict(from_attributes=True)
