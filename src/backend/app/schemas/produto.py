from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


# 1. Campos base compartilhados (alinhados aos tamanhos reais do SQL)
class ProdutoBase(BaseModel):
    nome: str = Field(..., max_length=255, description="Nome descritivo do produto")
    sku: Optional[str] = Field(None, max_length=150, description="Código identificador único (SKU)")
    fabrica_id: int = Field(..., description="ID da fábrica associada")

    model_config = ConfigDict(str_strip_whitespace=True)

# 4. Resposta da API pronta para o React
class ProdutoResponse(ProdutoBase):
    id: int
    nome_fabrica: Optional[str] = Field(None, description="Nome da fábrica para exibição direta")

    model_config = ConfigDict(from_attributes=True)