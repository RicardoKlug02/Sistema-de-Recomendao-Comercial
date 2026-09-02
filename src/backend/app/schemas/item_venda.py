from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, computed_field


# 1. Campos base compartilhados
class ItemVendaBase(BaseModel):
    produto_id: int = Field(..., description="ID do produto vendido")
    quantidade: int = Field(..., gt=0, description="Quantidade vendida (deve ser maior que zero)")
    preco_unitario: float = Field(..., gt=0.0, description="Preço unitário cobrado (deve ser maior que zero)")


# 2. Schema para criação individual ou em lote (POST /itens_venda)
class ItemVendaCreate(ItemVendaBase):
    venda_id: Optional[int] = Field(None, description="ID da venda (opcional caso seja enviado dentro do payload da venda)")


# 3. Schema para atualização parcial (PATCH /itens_venda/{id})
class ItemVendaUpdate(BaseModel):
    produto_id: Optional[int] = None
    quantidade: Optional[int] = Field(None, gt=0)
    preco_unitario: Optional[float] = Field(None, gt=0.0)


# 4. Schema para leitura/resposta da API (GET /itens_venda/{id})
class ItemVendaResponse(ItemVendaBase):
    id: int
    venda_id: int

    @computed_field
    @property
    def subtotal(self) -> float:
        return round(self.quantidade * self.preco_unitario, 2)

    model_config = ConfigDict(from_attributes=True)