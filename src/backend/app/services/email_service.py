from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
from pydantic import EmailStr

# Configuração SMTP da empresa
conf = ConnectionConfig(
    MAIL_USERNAME="seu_email@empresa.com",
    MAIL_PASSWORD="senha_de_app_ou_token",
    MAIL_FROM="seu_email@empresa.com",
    MAIL_PORT=587,
    MAIL_SERVER="smtp.gmail.com", 
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
)


class EmailService:

    def __init__(self):
        self.mail = FastMail(conf)

    async def enviar_solicitacao_aprovacao(
        self,
        email_admin: EmailStr,
        nome_solicitante: str,
        email_solicitante: str,
        token_aprovacao: str,
        base_url: str = "http://localhost:8000",
    ):
        """Dispara um e-mail com botão de clique único para o gestor aprovar o acesso."""
        link_aprovacao = (
            f"{base_url}/api/v1/auth/aprovar?token={token_aprovacao}"
        )

        corpo_html = f"""
        <html>
            <body style="font-family: Arial, sans-serif; color: #333; line-height: 1.6;">
                <h2 style="color: #0056b3;">Novo Cadastro Aguardando Aprovação</h2>
                <p>Um novo vendedor solicitou acesso ao <strong>Sistema de Inteligência Comercial</strong>:</p>
                <ul>
                    <li><strong>Nome:</strong> {nome_solicitante}</li>
                    <li><strong>E-mail:</strong> {email_solicitante}</li>
                </ul>
                <p>Para autorizar o acesso a dados de vendas, carteira e dados protegidos por LGPD, clique no botão abaixo:</p>
                <p style="margin: 25px 0;">
                    <a href="{link_aprovacao}" 
                       style="background-color: #28a745; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; font-weight: bold;">
                        Aprovar Acesso de {nome_solicitante}
                    </a>
                </p>
                <p style="font-size: 12px; color: #888;">
                    Este link é válido por 48 horas.<br>
                    Se o botão não funcionar, copie este link no navegador:<br>
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