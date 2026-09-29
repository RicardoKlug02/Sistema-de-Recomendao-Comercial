from pathlib import Path
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from cryptography.fernet import Fernet


class Settings(BaseSettings):
    DEBUG: bool = False
    API_VERSION: str = "v1"
    BACKEND_URL: str = "http://localhost:8000"
    FRONTEND_URL: str = "http://localhost:5173"
    ADMIN_EMAIL: str = "admin@example.com"
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]
    DATABASE_URL: str
    JWT_SECRET_KEY: str
    CHAVE_SERIALIZER: str
    BLIND_INDEX_SALT: str
    SECRET_ENCRYPTION_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480
<<<<<<< Updated upstream
    SECRET_ENCRYPTION_KEY: str

    # SMTP FastMail
    EMAIL_PROVEDOR: str = "smtp"
    RESEND_API_KEY: str = ""
=======
    MAIL_ENABLED: bool = False
>>>>>>> Stashed changes
    MAIL_USERNAME: str = ""
    MAIL_PASSWORD: str = ""
    MAIL_FROM: str = "noreply@example.com"
    MAIL_PORT: int = 587
    MAIL_SERVER: str = "localhost"
    MAIL_STARTTLS: bool = True
    MAIL_SSL_TLS: bool = False
    MAIL_USE_CREDENTIALS: bool = True

    @field_validator("JWT_SECRET_KEY", "CHAVE_SERIALIZER", "BLIND_INDEX_SALT")
    @classmethod
    def validar_segredo(cls, valor):
        if len(valor) < 32 or valor.startswith(("sua_", "troque_")):
            raise ValueError("Gere segredos próprios com scripts/configurar.py.")
        return valor

    @field_validator("SECRET_ENCRYPTION_KEY")
    @classmethod
    def validar_cifra(cls, valor):
        Fernet(valor.encode())
        return valor

    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[4] / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
