<<<<<<< Updated upstream
import asyncio
import logging
from html import escape
from urllib.parse import urlencode, urlsplit

import httpx
=======
from html import escape
>>>>>>> Stashed changes
from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
from pydantic import EmailStr, TypeAdapter

from src.backend.app.core.config import settings

registro = logging.getLogger(__name__)


class ErroEnvioEmail(Exception):
    """Falha de configuração ou entrega, sem expor credenciais ao cliente."""


class EmailService:
<<<<<<< Updated upstream
=======
    def __init__(self):
        self.conf = ConnectionConfig(
            MAIL_USERNAME=settings.MAIL_USERNAME,
            MAIL_PASSWORD=settings.MAIL_PASSWORD,
            MAIL_FROM=settings.MAIL_FROM,
            MAIL_PORT=settings.MAIL_PORT,
            MAIL_SERVER=settings.MAIL_SERVER,
            MAIL_STARTTLS=settings.MAIL_STARTTLS,
            MAIL_SSL_TLS=settings.MAIL_SSL_TLS,
            USE_CREDENTIALS=settings.MAIL_USE_CREDENTIALS,
        )
        self.mail = FastMail(self.conf)

>>>>>>> Stashed changes
    async def enviar_solicitacao_aprovacao(
        self,
        email_admin: str,
        nome_solicitante: str,
        email_solicitante: str,
        token_aprovacao: str,
        base_url: str = None,
    ):
<<<<<<< Updated upstream
        """Envia a aprovação via HTTPS ou SMTP, com tempo de espera limitado."""
        try:
            destinatario = str(TypeAdapter(EmailStr).validate_python(email_admin))
            remetente = str(TypeAdapter(EmailStr).validate_python(settings.MAIL_FROM))
            origem = (base_url or settings.BACKEND_URL).rstrip("/")
            endereco = urlsplit(origem)
            if endereco.scheme not in ("http", "https") or not endereco.hostname or endereco.query or endereco.fragment or endereco.username:
                raise ValueError("BACKEND_URL inválida")
            link = f"{origem}/api/v1/auth/aprovar?{urlencode({'token': token_aprovacao})}"
            nome = escape(nome_solicitante)
            corpo = (
                '<h2>Novo cadastro aguardando aprovação</h2>'
                f'<p><strong>{nome}</strong> ({escape(email_solicitante)}) solicitou acesso ao sistema.</p>'
                f'<p><a href="{escape(link, quote=True)}">Aprovar acesso</a></p>'
                '<p>Este link é válido por 48 horas.</p>'
            )
            assunto = "Rio Verde — Cadastro aguardando aprovação"
            async with asyncio.timeout(20):
                if settings.EMAIL_PROVEDOR == "resend":
                    if not settings.RESEND_API_KEY:
                        raise ValueError("RESEND_API_KEY não configurada")
                    async with httpx.AsyncClient(timeout=15) as cliente:
                        resposta = await cliente.post(
                            "https://api.resend.com/emails",
                            headers={"Authorization": f"Bearer {settings.RESEND_API_KEY}"},
                            json={"from": remetente, "to": [destinatario], "subject": assunto, "html": corpo},
                        )
                        resposta.raise_for_status()
                        if not resposta.json().get("id"):
                            raise ValueError("Provedor não confirmou o envio")
                elif settings.EMAIL_PROVEDOR == "smtp":
                    if not settings.MAIL_USERNAME or not settings.MAIL_PASSWORD:
                        raise ValueError("Credenciais SMTP não configuradas")
                    # Configuração tardia: uma falha no e-mail não impede iniciar a API.
                    configuracao = ConnectionConfig(
                        MAIL_USERNAME=settings.MAIL_USERNAME,
                        MAIL_PASSWORD=settings.MAIL_PASSWORD,
                        MAIL_FROM=remetente,
                        MAIL_PORT=settings.MAIL_PORT,
                        MAIL_SERVER=settings.MAIL_SERVER,
                        MAIL_STARTTLS=settings.MAIL_STARTTLS,
                        MAIL_SSL_TLS=settings.MAIL_SSL_TLS,
                        USE_CREDENTIALS=True,
                        TIMEOUT=15,
                    )
                    await FastMail(configuracao).send_message(MessageSchema(
                        subject=assunto, recipients=[destinatario], body=corpo, subtype=MessageType.html,
                    ))
                else:
                    raise ValueError("EMAIL_PROVEDOR inválido")
        except Exception as erro:
            # Não registrar corpo, token, senha ou resposta do provedor.
            codigo = erro.response.status_code if isinstance(erro, httpx.HTTPStatusError) else None
            registro.error("Falha no envio de aprovação: provedor=%s tipo=%s status=%s", settings.EMAIL_PROVEDOR, type(erro).__name__, codigo)
            raise ErroEnvioEmail("Não foi possível enviar o e-mail de aprovação.") from erro
=======
        """Dispara e-mail com link assinado para aprovação de novo cadastro."""
        origem = base_url or getattr(settings, "BACKEND_URL", "http://localhost:8000")
        link_aprovacao = f"{origem}/api/v1/auth/aprovar?token={token_aprovacao}"

        nome_solicitante = escape(nome_solicitante)
        email_solicitante = escape(email_solicitante)
        corpo_html = f"""
        <html>
            <body style="font-family: Arial, sans-serif; color: #333; line-height: 1.6;">
                <h2 style="color: #0056b3;">Novo Cadastro Aguardando Aprovação</h2>
                <p>Um novo colaborador solicitou acesso ao <strong>Sistema de Inteligência Comercial</strong>:</p>
                <ul>
                    <li><strong>Nome:</strong> {nome_solicitante}</li>
                    <li><strong>E-mail:</strong> {email_solicitante}</li>
                </ul>
                <p>Para autorizar o acesso à carteira de clientes e métricas, clique no botão abaixo:</p>
                <p style="margin: 25px 0;">
                    <a href="{link_aprovacao}" 
                       style="background-color: #28a745; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; font-weight: bold; display: inline-block;">
                        Aprovar Acesso de {nome_solicitante}
                    </a>
                </p>
                <p style="font-size: 12px; color: #888;">
                    Este link é válido por tempo limitado.<br>
                    Se o botão não funcionar, acesse diretamente:<br>
                    {link_aprovacao}
                </p>
            </body>
        </html>
        """

        mensagem = MessageSchema(
            subject=f"[Aprovação Necessária] Novo usuário: {nome_solicitante}",
            recipients=[email_admin],
            body=corpo_html,
            subtype=MessageType.html,
        )

        await self.mail.send_message(mensagem)

    async def enviar_recuperacao(self, email: str, token: str):
        link = f"{settings.FRONTEND_URL}/#/redefinir?token={token}"
        mensagem = MessageSchema(
            subject="Recuperação de senha — Rio Verde",
            recipients=[email],
            body=f'<p>Para criar uma nova senha, <a href="{escape(link, quote=True)}">acesse este link</a>.</p><p>Válido por 30 minutos. Se não solicitou, ignore a mensagem.</p>',
            subtype=MessageType.html,
        )
        await self.mail.send_message(mensagem)
>>>>>>> Stashed changes
