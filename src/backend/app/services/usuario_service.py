from typing import List, Optional
from sqlalchemy.orm import Session

from src.backend.app.core.security import gerar_hash_senha
from src.backend.app.models.usuario import Usuario


class UsuarioService:

    def __init__(self, db_session: Session):
        self.db = db_session

    def criar_usuario(
        self, nome: str, email: str, senha_plana: str
    ) -> Usuario:
        email_normalizado = email.strip().lower()

        existente = (
            self.db.query(Usuario)
            .filter(Usuario.email == email_normalizado)
            .first()
        )
        if existente:
            raise ValueError(f"O e-mail '{email_normalizado}' já está cadastrado.")

        novo_usuario = Usuario(
            nome=nome.strip(),
            email=email_normalizado,
            senha_hash=gerar_hash_senha(senha_plana),
            ativo=True,
        )
        self.db.add(novo_usuario)
        self.db.commit()
        self.db.refresh(novo_usuario)
        return novo_usuario

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
            query = query.filter(Usuario.ativo == True)
        return query.all()

    def desativar_usuario(self, usuario_id: int) -> bool:
        usuario = self.buscar_por_id(usuario_id)
        if not usuario:
            return False
        usuario.ativo = False
        self.db.commit()
        return True