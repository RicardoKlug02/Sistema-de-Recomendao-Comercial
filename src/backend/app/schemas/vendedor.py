from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


# 1. Campos base compartilhados
class VendedorBase(BaseModel):
    nome: str = Field(..., min_length=1, max_length=100, description="Nome completo do vendedor / representante")

    model_config = ConfigDict(str_strip_whitespace=True)

# 2. Resposta da API (GET /vendedores/{id})
class VendedorResponse(VendedorBase):
    id: int

    model_config = ConfigDict(from_attributes=True)