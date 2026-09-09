from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from src.backend.app.core.database import get_db
from src.backend.app.core.security import decodificar_token_acesso
from src.backend.app.models.usuario import Usuario
from src.backend.app.services.usuario_service import UsuarioService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_usuario_atual(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
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

    service = UsuarioService(db_session=db)
    usuario = service.buscar_por_email(email)

    if not usuario:
        raise credenciais_exception

    if not usuario.ativo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuário inativo no sistema.",
        )

    return usuario