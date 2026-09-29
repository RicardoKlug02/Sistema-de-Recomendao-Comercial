from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, computed_field


class ItemVendaBase(BaseModel):
    produto_id: int = Field(..., description="ID do produto vendido")
    quantidade: int = Field(..., gt=0, description="Quantidade vendida (maior que zero)")
    preco_unitario: float = Field(..., gt=0.0, description="Preço unitário cobrado (maior que zero)")


# Leitura / Resposta da API
class ItemVendaResponse(ItemVendaBase):
    id: int
    venda_id: int
    nome_produto: Optional[str] = Field(None, description="Nome do produto para facilitar exibição no front")

    subtotal: float

    model_config = ConfigDict(from_attributes=True)