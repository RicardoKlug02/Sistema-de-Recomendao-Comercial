import os
from cryptography.fernet import Fernet

ENCRYPTION_KEY = os.getenv("SECRET_ENCRYPTION_KEY")
# Garante fallback durante desenvolvimento inicial
fernet = Fernet(ENCRYPTION_KEY.encode()) if ENCRYPTION_KEY else None


def encrypt_data(plain_text: str) -> str:
    """Criptografa o texto legível para salvar no banco."""
    if not plain_text or not fernet:
        return plain_text
    return fernet.encrypt(plain_text.strip().encode("utf-8")).decode("utf-8")


def decrypt_data(cipher_text: str) -> str:
    """Descriptografa o conteúdo do banco para exibir na API."""
    if not cipher_text or not fernet:
        return cipher_text
    try:
        return fernet.decrypt(cipher_text.encode("utf-8")).decode("utf-8")
    except Exception:
        return cipher_text  # Retorna o original se falhar ou se já for texto plano