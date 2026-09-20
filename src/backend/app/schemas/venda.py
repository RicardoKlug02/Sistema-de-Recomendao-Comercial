from datetime import date
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field

# Ajuste o import conforme sua estrutura
from src.backend.app.schemas.item_venda import ItemVendaBase, ItemVendaResponse


# 1. Campos base compartilhados
class VendaBase(BaseModel):
    numero_pedido: str = Field(..., description="Número do pedido")
    cliente_id: int = Field(..., description="ID do cliente")
    vendedor_id: Optional[int] = Field(None, description="ID do vendedor/representante")
    fabrica_id: int = Field(..., description="ID da fábrica faturadora")
    data_venda: date = Field(..., description="Data da realização da venda (AAAA-MM-DD)")
    valor_total: float = Field(0.0, ge=0.0, description="Valor total da venda")

    model_config = ConfigDict(str_strip_whitespace=True)

# 4. Leitura básica / listagem simples (GET /vendas)
class VendaResponse(VendaBase):
    id: int
    cliente_nome: Optional[str] = Field(None, description="Razão social para exibição no front")
    fabrica_nome: Optional[str] = Field(None, description="Nome da fábrica para exibição no front")
    vendedor_nome: Optional[str] = Field(None, description="Nome do vendedor")

    model_config = ConfigDict(from_attributes=True)


# 5. Leitura detalhada com a lista de itens (GET /vendas/{id})
class VendaDetalhadaResponse(VendaResponse):
    itens: List[ItemVendaResponse] = []