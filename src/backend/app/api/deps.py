from typing import Generator
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from src.backend.app.core.database import get_db
from src.backend.app.core.security import decodificar_token_acesso
from src.backend.app.models.usuario import Usuario
from src.backend.app.services.auth_service import AuthService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_usuario_atual(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> Usuario:
    """Extrai e valida o usuário a partir do token JWT Bearer."""
    credenciais_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciais inválidas ou token expirado.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decodificar_token_acesso(token)
    if not payload:
        raise credenciais_exception

    email: str = payload.get("sub")
    if not email:
        raise credenciais_exception

    auth_service = AuthService(db_session=db)
    usuario = auth_service.buscar_por_email(email)

    if not usuario:
        raise credenciais_exception

    if not usuario.ativo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuário inativo no sistema.",
        )

    if not usuario.aprovado:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cadastro aguardando aprovação do administrador.",
        )

    return usuario


def get_usuario_admin(
    usuario_atual: Usuario = Depends(get_usuario_atual),
) -> Usuario:
    """Exige privilégios de gestor/administrador para a rota."""
    if usuario_atual.perfil not in ["admin", "gestor"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso restrito a administradores.",
        )
    return usuario_atual