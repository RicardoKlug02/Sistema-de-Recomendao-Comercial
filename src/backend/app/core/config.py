from pathlib import Path
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_FILE_PATH = Path(__file__).resolve().parents[4] / ".env"


class Settings(BaseSettings):
    # App
    DEBUG: bool = True
    API_VERSION: str = "v1"
    BACKEND_URL: str = "http://localhost:8000"
    ADMIN_EMAIL: str = "diretor@empresa.com"
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ]

    # Banco de Dados
    DATABASE_URL: str
    DB_HOST: str = "localhost"
    DB_PORT: str = "5432"
    DB_NAME: str = "meubanco_tcc"
    DB_USER: str = "postgres"
    DB_PASSWORD: str = "postgres"

    # Segurança
    SECRET_KEY: str
    JWT_SECRET_KEY: str
    CHAVE_SERIALIZER: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480
    SECRET_ENCRYPTION_KEY: str

    # SMTP FastMail
    MAIL_USERNAME: str = ""
    MAIL_PASSWORD: str = ""
    MAIL_FROM: str = ""
    MAIL_PORT: int = 587
    MAIL_SERVER: str = "smtp.gmail.com"
    MAIL_STARTTLS: bool = True
    MAIL_SSL_TLS: bool = False

    # Configuração Pydantic V2
    model_config = SettingsConfigDict(
        env_file=ENV_FILE_PATH,
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()