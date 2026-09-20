from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import HTMLResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from src.backend.app.core.config import settings
from src.backend.app.core.database import get_db
from src.backend.app.core.security import (
    gerar_token_aprovacao,
    validar_token_aprovacao,
)
from src.backend.app.schemas.auth import LoginRequest, RegistroUsuarioRequest, TokenResponse
from src.backend.app.services.auth_service import AuthService
from src.backend.app.services.email_service import EmailService

router = APIRouter(prefix="/auth", tags=["Autenticação"])
email_service = EmailService()


@router.post("/login", response_model=TokenResponse)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """Autenticação compatível com OAuth2 Password Flow (Swagger e React)."""
    service = AuthService(db_session=db)
    usuario = service.autenticar(
        email=form_data.username, senha_plana=form_data.password
    )

    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail ou senha incorretos, ou cadastro ainda pendente de aprovação.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return service.gerar_sessao(usuario)


@router.post("/registrar", status_code=status.HTTP_201_CREATED)
async def registrar_usuario(
    dados: RegistroUsuarioRequest,
    db: Session = Depends(get_db),
):
    """Cadastra usuário bloqueado e dispara e-mail com link de autorização para o gestor."""
    service = AuthService(db_session=db)

    try:
        novo_usuario = service.criar_usuario(
            nome=dados.nome,
            email=dados.email,
            senha_plana=dados.senha,
            perfil="vendedor",
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    token = gerar_token_aprovacao(novo_usuario.id)

    email_destino = getattr(settings, "ADMIN_EMAIL", "diretor@empresa.com")
    await email_service.enviar_solicitacao_aprovacao(
        email_admin=email_destino,
        nome_solicitante=novo_usuario.nome,
        email_solicitante=novo_usuario.email,
        token_aprovacao=token,
    )

    return {
        "mensagem": "Cadastro realizado com sucesso! Aguarde a aprovação do administrador por e-mail."
    }


@router.get("/aprovar", response_class=HTMLResponse)
def aprovar_usuario_via_link(
    token: str = Query(..., description="Token de aprovação recebido por e-mail"),
    db: Session = Depends(get_db),
):
    """Ativa o usuário quando o gestor clica no link do e-mail."""
    try:
        usuario_id = validar_token_aprovacao(token, max_horas=48)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    service = AuthService(db_session=db)
    sucesso = service.aprovar_usuario(usuario_id)

    if not sucesso:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado para aprovação.",
        )

    return """
    <html>
        <body style="font-family: Arial, sans-serif; display: flex; justify-content: center; align-items: center; height: 80vh; background-color: #f8f9fa;">
            <div style="background: white; padding: 40px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); text-align: center; max-width: 420px;">
                <h2 style="color: #28a745;">Acesso Autorizado!</h2>
                <p style="color: #555;">O usuário foi aprovado e já pode efetuar login na plataforma.</p>
            </div>
        </body>
    </html>
    """