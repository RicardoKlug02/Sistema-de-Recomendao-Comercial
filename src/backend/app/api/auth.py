import hashlib
import logging
from html import escape
from fastapi import APIRouter, Depends, HTTPException, Query, Form
from fastapi.responses import HTMLResponse
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session
from itsdangerous import BadSignature, SignatureExpired
from src.backend.app.core.config import settings
from src.backend.app.core.database import get_db
from src.backend.app.core.security import (
    gerar_token_aprovacao,
    validar_token_aprovacao,
    serializer,
    gerar_hash_senha,
    verificar_senha,
)
from src.backend.app.schemas.auth import RegistroUsuarioRequest, TokenResponse
from src.backend.app.services.auth_service import AuthService
<<<<<<< Updated upstream
from src.backend.app.services.email_service import EmailService, ErroEnvioEmail
=======
from src.backend.app.services.email_service import EmailService
from src.backend.app.api.deps import get_usuario_atual
from src.backend.app.models.usuario import Usuario
>>>>>>> Stashed changes

router = APIRouter(prefix="/auth", tags=["Autenticação"])
log = logging.getLogger(__name__)


class EmailRequest(BaseModel):
    email: EmailStr


class SenhaRequest(BaseModel):
    senha: str = Field(min_length=10, max_length=72)


class ResetRequest(SenhaRequest):
    token: str


class AlterarSenhaRequest(SenhaRequest):
    senha_atual: str


def senha_hash(senha):
    try:
        return gerar_hash_senha(senha)
    except ValueError as e:
        raise HTTPException(422, str(e))


@router.post("/login", response_model=TokenResponse)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    service = AuthService(db)
    usuario = service.autenticar(form_data.username, form_data.password)
    if not usuario:
        raise HTTPException(
            401,
            "E-mail ou senha incorretos, ou cadastro ainda pendente de aprovação.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return service.gerar_sessao(usuario)


<<<<<<< Updated upstream
@router.post("/registrar", status_code=status.HTTP_201_CREATED)
async def registrar_usuario(
    dados: RegistroUsuarioRequest,
    db: Session = Depends(get_db),
):
    """Cadastra usuário bloqueado e dispara e-mail com link de autorização para o gestor."""
    service = AuthService(db_session=db)

    try:
        novo_usuario = service.solicitar_cadastro(
            nome=dados.nome,
            email=dados.email,
            senha=dados.senha,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    token = gerar_token_aprovacao(novo_usuario.id)

    try:
        await email_service.enviar_solicitacao_aprovacao(
            email_admin=settings.ADMIN_EMAIL,
            nome_solicitante=novo_usuario.nome,
            email_solicitante=novo_usuario.email,
            token_aprovacao=token,
        )
    except ErroEnvioEmail as erro:
        # O cadastro permanece bloqueado; uma nova tentativa exige a mesma senha.
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=("Seu cadastro está salvo, mas não foi possível enviar o e-mail de aprovação. "
                    "Contate o administrador e, após a correção do envio, repita o cadastro "
                    "com o mesmo e-mail e senha. Seu acesso ainda não foi liberado."),
        ) from erro
=======
@router.get("/me")
def me(usuario: Usuario = Depends(get_usuario_atual)):
    return dict(
        id=usuario.id, nome=usuario.nome, email=usuario.email, perfil=usuario.perfil
    )
>>>>>>> Stashed changes


@router.post("/registrar", status_code=201)
async def registrar(dados: RegistroUsuarioRequest, db: Session = Depends(get_db)):
    if len(dados.senha.encode()) > 72:
        raise HTTPException(422, "A senha deve ter até 72 bytes.")
    try:
        usuario = AuthService(db).criar_usuario(dados.nome, dados.email, dados.senha)
    except ValueError as e:
        raise HTTPException(400, str(e))
    mensagem = "Cadastro realizado. Aguarde a aprovação de um administrador."
    if settings.MAIL_ENABLED:
        try:
            await EmailService().enviar_solicitacao_aprovacao(
                settings.ADMIN_EMAIL,
                usuario.nome,
                usuario.email,
                gerar_token_aprovacao(usuario.id),
            )
        except Exception:
            log.warning(
                "Falha no envio da solicitação de aprovação; cadastro disponível na gestão de usuários."
            )
            mensagem += " O aviso por e-mail não pôde ser enviado; solicite a aprovação pela equipe responsável."
    return {"mensagem": mensagem}


@router.get("/aprovar", response_class=HTMLResponse)
def confirmar_aprovacao(token: str = Query(...)):
    try:
        validar_token_aprovacao(token, max_horas=48)
    except ValueError as e:
        raise HTTPException(400, str(e))
    return f'<html lang="pt-BR"><head><title>Aprovar acesso</title></head><body><h1>Confirmar aprovação</h1><p>Aprove somente cadastros esperados por sua equipe.</p><form method="post"><input type="hidden" name="token" value="{escape(token, quote=True)}"><button>Confirmar aprovação do usuário</button></form></body></html>'


@router.post("/aprovar", response_class=HTMLResponse)
def aprovar(token: str = Form(...), db: Session = Depends(get_db)):
    try:
        id_usuario = validar_token_aprovacao(token, max_horas=48)
    except ValueError as e:
        raise HTTPException(400, str(e))
    u = db.query(Usuario).filter_by(id=id_usuario).with_for_update().first()
    if not u:
        raise HTTPException(404, "Usuário não encontrado.")
    if u.aprovado:
        raise HTTPException(409, "Este cadastro já foi aprovado.")
    u.aprovado = True
    db.commit()
    return '<html lang="pt-BR"><body><h1>Acesso aprovado</h1><p>O usuário já pode entrar na plataforma.</p></body></html>'


@router.post("/recuperar")
async def recuperar(dados: EmailRequest, db: Session = Depends(get_db)):
    if not settings.MAIL_ENABLED:
        raise HTTPException(
            503, "Recuperação por e-mail indisponível. Contate o administrador."
        )
    u = AuthService(db).buscar_por_email(str(dados.email))
    if u and u.ativo and u.aprovado:
        token = serializer.dumps(
            {"id": u.id, "senha": hashlib.sha256(u.senha_hash.encode()).hexdigest()},
            salt="recuperacao-senha",
        )
        try:
            await EmailService().enviar_recuperacao(u.email, token)
        except Exception:
            log.warning("Falha no envio de recuperação de senha.")
            raise HTTPException(
                503,
                "Não foi possível enviar a recuperação. Tente novamente mais tarde.",
            )
    return {
        "mensagem": "Se houver uma conta ativa com esse e-mail, você receberá um link de recuperação válido por 30 minutos."
    }


@router.post("/redefinir")
def redefinir(dados: ResetRequest, db: Session = Depends(get_db)):
    try:
        payload = serializer.loads(dados.token, salt="recuperacao-senha", max_age=1800)
    except (BadSignature, SignatureExpired):
        raise HTTPException(400, "Link inválido ou expirado.")
    u = db.query(Usuario).filter_by(id=payload["id"]).with_for_update().first()
    if (
        not u
        or not u.ativo
        or not u.aprovado
        or payload["senha"] != hashlib.sha256(u.senha_hash.encode()).hexdigest()
    ):
        raise HTTPException(400, "Link inválido ou já utilizado.")
    u.senha_hash = senha_hash(dados.senha)
    u.versao_sessao += 1
    db.commit()
    return {"mensagem": "Senha alterada."}


@router.post("/senha")
def alterar_senha(
    dados: AlterarSenhaRequest,
    u: Usuario = Depends(get_usuario_atual),
    db: Session = Depends(get_db),
):
<<<<<<< Updated upstream
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
=======
    if not verificar_senha(dados.senha_atual, u.senha_hash):
        raise HTTPException(400, "Senha atual incorreta.")
    u.senha_hash = senha_hash(dados.senha)
    u.versao_sessao += 1
    db.commit()
    return {"mensagem": "Senha alterada. Entre novamente."}
>>>>>>> Stashed changes
