from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from src.backend.app.core.security import criar_token_acesso, gerar_hash_senha, verificar_senha
from src.backend.app.models.usuario import Usuario


class AuthService:

    def __init__(self, db_session: Session):
        self.db = db_session

    # --- Métodos de Consulta e Ciclo de Vida do Usuário ---

    def buscar_por_email(self, email: str) -> Optional[Usuario]:
        return (
            self.db.query(Usuario)
            .filter(Usuario.email == email.strip().lower())
            .first()
        )

    def buscar_por_id(self, usuario_id: int) -> Optional[Usuario]:
        return self.db.query(Usuario).filter(Usuario.id == usuario_id).first()

    def listar_usuarios(self, apenas_ativos: bool = True) -> List[Usuario]:
        query = self.db.query(Usuario)
        if apenas_ativos:
            query = query.filter(Usuario.ativo.is_(True))
        return query.all()

    def criar_usuario(
        self, nome: str, email: str, senha_plana: str, perfil: str = "vendedor"
    ) -> Usuario:
        email_normalizado = email.strip().lower()

        existente = self.buscar_por_email(email_normalizado)
        if existente:
            raise ValueError(f"O e-mail '{email_normalizado}' já está cadastrado.")

        novo_usuario = Usuario(
            nome=nome.strip(),
            email=email_normalizado,
            senha_hash=gerar_hash_senha(senha_plana),
            perfil=perfil,
            ativo=True,
            aprovado=False,  # Aguarda aprovação do administrador
        )
        self.db.add(novo_usuario)
        self.db.commit()
        self.db.refresh(novo_usuario)
        return novo_usuario

    def aprovar_usuario(self, usuario_id: int) -> bool:
        usuario = self.buscar_por_id(usuario_id)
        if not usuario:
            return False
        usuario.aprovado = True
        self.db.commit()
        return True

    def desativar_usuario(self, usuario_id: int) -> bool:
        usuario = self.buscar_por_id(usuario_id)
        if not usuario:
            return False
        usuario.ativo = False
        self.db.commit()
        return True

    # --- Autenticação e Sessão JWT ---

    def autenticar(self, email: str, senha_plana: str) -> Optional[Usuario]:
        """Localiza o usuário e valida senha, status ativo e aprovação."""
        usuario = self.buscar_por_email(email)
        if not usuario or not usuario.ativo or not usuario.aprovado:
            return None

        if not verificar_senha(senha_plana, usuario.senha_hash):
            return None

        return usuario

    def gerar_sessao(self, usuario: Usuario) -> Dict[str, Any]:
        """Gera o payload do token de acesso formatado para o React."""
        token = criar_token_acesso(
            dados={
                "sub": usuario.email,
                "id": usuario.id,
                "perfil": usuario.perfil,
            }
        )
        return {
            "access_token": token,
            "token_type": "bearer",
            "usuario_nome": usuario.nome,
            "usuario_email": usuario.email,
            "usuario_perfil": usuario.perfil,
        }