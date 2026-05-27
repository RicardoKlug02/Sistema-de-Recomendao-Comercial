from pydantic import BaseModel
from typing import Optional

# Esse schema é usado quando você vai criar um cliente novo
class ClienteCreate(BaseModel):
    nome: str
    segmento: str
    cidade: str
    estado: str

# Esse schema é usado quando você vai devolver o cliente para o Front (leitura)
class ClienteResponse(ClienteCreate):
    id: int

    class Config:
        from_attributes = True # Permite ler objetos do SQLAlchemy