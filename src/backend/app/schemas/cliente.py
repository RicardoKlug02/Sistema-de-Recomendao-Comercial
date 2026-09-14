from pydantic import BaseModel, ConfigDict
from typing import Optional

# Usado para entrada de dados (POST /clientes)
class ClienteCreate(BaseModel):
    nome: str
    segmento: str
    cidade: str
    estado: str

# Usado para envio ao frontend (GET /clientes/{id})
class ClienteResponse(ClienteCreate):
    id: int

    model_config = ConfigDict(from_attributes=True)

class ClienteFichaMetricasOut(BaseModel):
    id: int
    razao_social: str
    cnpj: str
    regiao: str
    vendas_ultimo_mes: float
    pedidos_ultimo_mes: int

    class Config:
        from_attributes = True

from pydantic import BaseModel
from typing import List, Optional

class ItemResumo(BaseModel):
    produto_id: int
    nome_produto: str
    quantidade: int
    valor_total: float
    ultima_compra: Optional[str] = None

class RecomendacaoItem(BaseModel):
    produto_id: int
    nome_produto: str
    motivo: str # ex: "Mais vendido na sua região", "Reposição recomendada"
    score_relevancia: float

class RelatorioComplexoClienteOut(BaseModel):
    # Ficha básica
    id: int
    razao_social: str
    cnpj: str
    regiao: str
    
    # Métricas do Mês Fechado
    mes_referencia: str # ex: "08/2026"
    vendas_mes_fechado: float
    pedidos_mes_fechado: int
    ticket_medio: float
    
    # Relatórios Analíticos
    itens_inclusos_ultimos_6m: List[ItemResumo]
    itens_inativos: List[ItemResumo] # Itens comprados no passado, mas sem pedido há > 90/180 dias
    recomendacoes: List[RecomendacaoItem] # Sugestões cruzadas por região ou perfil

    class Config:
        from_attributes = True