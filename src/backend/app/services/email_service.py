from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
from pydantic import EmailStr

from src.backend.app.core.config import settings


class EmailService:

    def __init__(self):
        self.conf = ConnectionConfig(
            MAIL_USERNAME=settings.MAIL_USERNAME,
            MAIL_PASSWORD=settings.MAIL_PASSWORD,
            MAIL_FROM=settings.MAIL_FROM,
            MAIL_PORT=settings.MAIL_PORT,
            MAIL_SERVER=settings.MAIL_SERVER,
            MAIL_STARTTLS=settings.MAIL_STARTTLS,
            MAIL_SSL_TLS=settings.MAIL_SSL_TLS,
            USE_CREDENTIALS=True,
        )
        self.mail = FastMail(self.conf)

    async def enviar_solicitacao_aprovacao(
        self,
        email_admin: EmailStr,
        nome_solicitante: str,
        email_solicitante: str,
        token_aprovacao: str,
        base_url: str = None,
    ):
        """Dispara e-mail com link assinado para aprovação de novo cadastro."""
        origem = base_url or getattr(settings, "BACKEND_URL", "http://localhost:8000")
        link_aprovacao = f"{origem}/api/v1/auth/aprovar?token={token_aprovacao}"

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