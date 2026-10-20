from typing import Any, Optional
from sqlalchemy.types import Text, TypeDecorator

from src.backend.app.core.security import encriptar_dado, decriptar_dado


class EncryptedString(TypeDecorator):
    """Tipo customizado que cifra no INSERT/UPDATE e decifra no SELECT.

    No banco de dados (PostgreSQL), a coluna opera como VARCHAR/TEXT contendo
    o token gerado pelo Fernet.
    No código Python, opera como uma string plana comum.
    """

    impl = Text
    cache_ok = True

    def __init__(self, length: int = 512, **kwargs: Any) -> None:
        # Reserva espaço suficiente para acomodar a expansão de tamanho do Fernet (Base64 + IV + HMAC)
        super().__init__(**kwargs)

    def process_bind_param(self, value: Optional[str], dialect: Any) -> Optional[str]:
        """Executado antes de salvar no banco de dados."""
        if value is not None:
            return encriptar_dado(str(value))
        return value

    def process_result_value(self, value: Optional[str], dialect: Any) -> Optional[str]:
        """Executado ao ler do banco de dados para a aplicação."""
        if value is not None:
            return decriptar_dado(str(value))
        return value
