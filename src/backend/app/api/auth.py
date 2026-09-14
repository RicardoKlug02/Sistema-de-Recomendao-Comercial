from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from src.backend.app.core.database import get_db
from src.backend.app.core.security import (
    gerar_token_aprovacao,
    validar_token_aprovacao,
)
from src.backend.app.schemas.auth import RegistroUsuarioRequest
from src.backend.app.services.email_service import EmailService
from src.backend.app.services.usuario_service import UsuarioService

router = APIRouter(prefix="/auth", tags=["Autenticação"])
email_service = EmailService()

EMAIL_ADMIN_EMPRESA = "diretor@empresa.com"  # E-mail que recebe os pedidos


@router.post("/registrar", status_code=status.HTTP_201_CREATED)
async def registrar_usuario(
    dados: RegistroUsuarioRequest, db: Session = Depends(get_db)
):
    """1. Vendedor se registra -> Salva bloqueado -> Envia link para o Admin."""
    service = UsuarioService(db_session=db)

    try:
        novo_usuario = service.registrar_novo_usuario(
            nome=dados.nome, email=dados.email, senha_plana=dados.senha
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Cria token seguro assinado para o link
    token = gerar_token_aprovacao(novo_usuario.id)

    # Dispara e-mail para o administrador responsável
    await email_service.enviar_solicitacao_aprovacao(
        email_admin=EMAIL_ADMIN_EMPRESA,
        nome_solicitante=novo_usuario.nome,
        email_solicitante=novo_usuario.email,
        token_aprovacao=token,
    )

    return {
        "mensagem": "Cadastro realizado com sucesso! Aguarde a aprovação do administrador por e-mail."
    }


@router.get("/aprovar")
def aprovar_usuario_via_link(
    token: str = Query(..., description="Token de aprovação recebido no e-mail"),
    db: Session = Depends(get_db),
):
    """2. Gestor clica no link do e-mail -> Ativa o usuário instantaneamente."""
    try:
        usuario_id = validar_token_aprovacao(token, max_horas=48)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    service = UsuarioService(db_session=db)
    sucesso = service.aprovar_usuario(usuario_id)

    if not sucesso:
        raise HTTPException(
            status_code=404, detail="Usuário não encontrado para aprovação."
        )

    return {
        "status": "sucesso",
        "mensagem": "Usuário aprovado com sucesso! O acesso já está liberado.",
    }