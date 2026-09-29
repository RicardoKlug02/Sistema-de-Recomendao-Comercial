from typing import Literal
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from src.backend.app.core.database import get_db
from src.backend.app.api.deps import get_usuario_admin
from src.backend.app.models.usuario import Usuario

router = APIRouter(prefix="/usuarios", tags=["Usuários"])


class EdicaoUsuario(BaseModel):
    perfil: Literal["admin", "gestor", "vendedor"] | None = None
    ativo: bool | None = None
    aprovado: bool | None = None


@router.get("")
def listar(db: Session = Depends(get_db), _: Usuario = Depends(get_usuario_admin)):
    return [
        dict(
            id=u.id,
            nome=u.nome,
            email=u.email,
            perfil=u.perfil,
            ativo=u.ativo,
            aprovado=u.aprovado,
        )
        for u in db.query(Usuario).order_by(Usuario.aprovado, Usuario.nome)
    ]


@router.patch("/{id_usuario}")
def editar(
    id_usuario: int,
    dados: EdicaoUsuario,
    db: Session = Depends(get_db),
    admin: Usuario = Depends(get_usuario_admin),
):
    u = db.get(Usuario, id_usuario)
    if not u:
        raise HTTPException(404, "Usuário não encontrado.")
    valores = dados.model_dump(exclude_none=True)
    if id_usuario == admin.id:
        raise HTTPException(400, "Não é permitido alterar seu próprio acesso.")
    if admin.perfil != "admin" and (u.perfil != "vendedor" or "perfil" in valores):
        raise HTTPException(
            403, "Apenas administradores podem gerenciar perfis privilegiados."
        )
    for chave, valor in valores.items():
        setattr(u, chave, valor)
    u.versao_sessao += 1
    db.commit()
    return {"mensagem": "Acesso atualizado."}
