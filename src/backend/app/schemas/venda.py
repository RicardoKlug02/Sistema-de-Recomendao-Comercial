from datetime import date
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field

# Importe o schema de item para permitir aninhamento
from src.backend.app.schemas.item_venda import ItemVendaBase, ItemVendaResponse


# 1. Campos base compartilhados
class VendaBase(BaseModel):
    cliente_id: int = Field(..., description="ID do cliente")
    vendedor_id: int = Field(..., description="ID do representante comercial / vendedor")
    fabrica_id: int = Field(..., description="ID da fábrica faturadora")
    data_venda: date = Field(..., description="Data da realização da venda (AAAA-MM-DD)")
    valor_total: Optional[float] = Field(None, ge=0.0, description="Valor total da venda")


# 2. Schema para criação (POST /vendas)
class VendaCreate(VendaBase):
    # Permite cadastrar a venda já acompanhada dos seus itens em uma única requisição
    itens: Optional[List[ItemVendaBase]] = Field(default_factory=list, description="Lista opcional de itens incluídos no pedido")


# 3. Schema para atualização parcial (PATCH /vendas/{id})
class VendaUpdate(BaseModel):
    cliente_id: Optional[int] = None
    vendedor_id: Optional[int] = None
    fabrica_id: Optional[int] = None
    data_venda: Optional[date] = None
    valor_total: Optional[float] = Field(None, ge=0.0)


# 4. Schema para leitura/resposta básica (GET /vendas/{id})
class VendaResponse(VendaBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


# 5. Schema detalhado com a lista de itens inclusos (Útil para tela de histórico de pedidos)
class VendaDetalhadaResponse(VendaResponse):
    itens: List[ItemVendaResponse] = []