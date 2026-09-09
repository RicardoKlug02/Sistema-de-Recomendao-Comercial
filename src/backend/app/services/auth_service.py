from typing import Optional
from sqlalchemy.orm import Session

from src.backend.app.core.security import criar_token_acesso, verificar_senha
from src.backend.app.models.usuario import Usuario
from src.backend.app.services.usuario_service import UsuarioService


class AuthService:

    def __init__(self, db_session: Session):
        self.db = db_session
        self.usuario_service = UsuarioService(db_session=db_session)

    def autenticar(self, email: str, senha_plana: str) -> Optional[Usuario]:
        """Localiza o usuário e valida o hash da senha."""
        usuario = self.usuario_service.buscar_por_email(email)
        if not usuario or not usuario.ativo:
            return None

        if not verificar_senha(senha_plana, usuario.senha_hash):
            return None

        return usuario

    def gerar_sessao(self, usuario: Usuario) -> dict:
        """Gera o token para o usuário validado."""
        token = criar_token_acesso(dados={"sub": usuario.email, "id": usuario.id})
        return {
            "access_token": token,
            "token_type": "bearer",
            "usuario_nome": usuario.nome,
            "usuario_email": usuario.email,
        }