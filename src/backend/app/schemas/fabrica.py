from typing import Optional
from pydantic import BaseModel, ConfigDict, Field

# 1. Campos base compartilhados
class FabricaBase(BaseModel):
    nome_fantasia: str = Field(..., max_length=100, description="Nome fantasia da fábrica")
    cnpj: Optional[str] = Field(None, max_length=18, description="CNPJ formatado ou apenas dígitos")


# 2. Schema para criação (POST /fabricas)
class FabricaCreate(FabricaBase):
    pass


# 3. Schema para atualização parcial (PATCH /fabricas/{id})
class FabricaUpdate(BaseModel):
    nome_fantasia: Optional[str] = Field(None, max_length=100)
    cnpj: Optional[str] = Field(None, max_length=18)


# 4. Schema para leitura/resposta simples (GET /fabricas/{id})
class FabricaResponse(FabricaBase):
    id: int

    model_config = ConfigDict(from_attributes=True)