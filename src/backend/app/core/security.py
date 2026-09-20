import hashlib
import hmac
import os
import re
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from cryptography.fernet import Fernet
from jose import JWTError, jwt
from passlib.context import CryptContext

from src.backend.app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

FERNET_CIPHER = Fernet(settings.SECRET_ENCRYPTION_KEY.encode("utf-8"))
BLIND_INDEX_SALT = getattr(settings, "BLIND_INDEX_SALT", settings.SECRET_KEY)


def gerar_hash_senha(senha: str) -> str:
    # Trunca em 72 bytes para evitar erro de buffer overflow do Bcrypt
    return pwd_context.hash(senha[:72])


def verificar_senha(senha_plana: str, senha_hash: str) -> bool:
    return pwd_context.verify(senha_plana[:72], senha_hash)


def encriptar_dado(dado: Optional[str]) -> Optional[str]:
    if not dado:
        return None
    return FERNET_CIPHER.encrypt(str(dado).encode("utf-8")).decode("utf-8")


def decriptar_dado(dado_cifrado: Optional[str]) -> Optional[str]:
    if not dado_cifrado:
        return None
    try:
        return FERNET_CIPHER.decrypt(dado_cifrado.encode("utf-8")).decode("utf-8")
    except Exception:
        return "[DADO CORROMPIDO]"


def gerar_blind_index(documento: Optional[str]) -> Optional[str]:
    """Gera hash determinístico para busca exata sem expor o CNPJ/CPF."""
    if not documento:
        return None
    doc_limpo = re.sub(r"\D", "", str(documento)).strip()
    if not doc_limpo:
        doc_limpo = str(documento).strip()
    if not doc_limpo:
        return None
    return hmac.new(
        BLIND_INDEX_SALT.encode("utf-8"),
        doc_limpo.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def criar_token_acesso(dados: Dict[str, Any], expira_em: Optional[timedelta] = None) -> str:
    payload = dados.copy()
    agora = datetime.now(timezone.utc)
    duracao = expira_em or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload.update({"iat": agora, "exp": agora + duracao})
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def verificar_token_acesso(token: str) -> Optional[Dict[str, Any]]:
    try:
        return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    except JWTError:
        return None