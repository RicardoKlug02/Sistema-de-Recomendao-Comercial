from pydantic import BaseModel, ConfigDict
from typing import Optional

# Usado para entrada de dados (POST /clientes)
class ClienteCreate(BaseModel):
    nome: str
    segmento: str
    cidade: str
    estado: str

# Usado para envio ao frontend (GET /clientes/{id})
class ClienteResponse(ClienteCreate):
    id: int

    model_config = ConfigDict(from_attributes=True)