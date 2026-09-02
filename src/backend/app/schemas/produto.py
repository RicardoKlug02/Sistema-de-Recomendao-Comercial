from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


# 1. Campos base compartilhados
class ProdutoBase(BaseModel):
    nome: str = Field(..., max_length=150, description="Nome descritivo do produto")
    sku: Optional[str] = Field(None, max_length=50, description="Código identificador único (SKU)")
    fabrica_id: int = Field(..., description="ID da fábrica associada ao produto")


# 2. Schema para criação (POST /produtos)
class ProdutoCreate(ProdutoBase):
    pass


# 3. Schema para atualização parcial (PATCH /produtos/{id})
class ProdutoUpdate(BaseModel):
    nome: Optional[str] = Field(None, max_length=150)
    sku: Optional[str] = Field(None, max_length=50)
    fabrica_id: Optional[int] = None


# 4. Schema para leitura/resposta da API (GET /produtos/{id})
class ProdutoResponse(ProdutoBase):
    id: int

    model_config = ConfigDict(from_attributes=True)