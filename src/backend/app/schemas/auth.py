from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr
    senha: str


class RegistroUsuarioRequest(BaseModel):
    nome: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    senha: str = Field(..., min_length=6, description="Senha com no mínimo 6 caracteres")


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    usuario_nome: str
    usuario_email: EmailStr
    usuario_perfil: str

    model_config = ConfigDict(from_attributes=True)