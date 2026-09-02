from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


# 1. Campos base compartilhados
class VendedorBase(BaseModel):
    nome: str = Field(..., min_length=1, max_length=100, description="Nome completo do vendedor / representante")


# 2. Schema para criação (POST /vendedores)
class VendedorCreate(VendedorBase):
    pass


# 3. Schema para atualização parcial (PATCH /vendedores/{id})
class VendedorUpdate(BaseModel):
    nome: Optional[str] = Field(None, min_length=1, max_length=100)


# 4. Schema para leitura/resposta da API (GET /vendedores/{id})
class VendedorResponse(VendedorBase):
    id: int

    model_config = ConfigDict(from_attributes=True)