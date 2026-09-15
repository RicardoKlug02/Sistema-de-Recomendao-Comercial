from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class FabricaBase(BaseModel):
    nome_fantasia: str = Field(..., max_length=100, description="Nome fantasia da fábrica")
    cnpj: Optional[str] = Field(None, max_length=18, description="CNPJ formatado ou apenas dígitos")

    model_config = ConfigDict(str_strip_whitespace=True)

class FabricaResponse(FabricaBase):
    id: int

    model_config = ConfigDict(from_attributes=True)