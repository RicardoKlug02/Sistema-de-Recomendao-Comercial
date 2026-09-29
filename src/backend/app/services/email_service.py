import asyncio
import logging
from html import escape
from urllib.parse import urlencode, urlsplit

import httpx
from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
from pydantic import EmailStr, TypeAdapter

from src.backend.app.core.config import settings

registro = logging.getLogger(__name__)


class ErroEnvioEmail(Exception):
    """Falha de configuração ou entrega, sem expor credenciais ao cliente."""


class EmailService:
    async def enviar_solicitacao_aprovacao(
        self,
        email_admin: str,
        nome_solicitante: str,
        email_solicitante: str,
        token_aprovacao: str,
        base_url: str = None,
    ):
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
