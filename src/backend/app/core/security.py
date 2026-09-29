import hashlib
import hmac
import os
import re
import bcrypt
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from cryptography.fernet import Fernet
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from jose import JWTError, jwt

from src.backend.app.core.config import settings

FERNET_CIPHER = Fernet(settings.SECRET_ENCRYPTION_KEY.encode("utf-8"))
BLIND_INDEX_SALT = getattr(settings, "BLIND_INDEX_SALT", settings.SECRET_KEY)


def gerar_hash_senha(senha: str) -> str:
    """Gera hash bcrypt com salt automático."""
    # Trunca em 72 bytes por especificação do algoritmo bcrypt
    senha_bytes = senha.encode("utf-8")[:72]
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(senha_bytes, salt).decode("utf-8")


def verificar_senha(senha_plana: str, senha_hash: str) -> bool:
    """Verifica se a senha em texto plano bate com o hash armazenado."""
    try:
        senha_bytes = senha_plana.encode("utf-8")[:72]
        hash_bytes = senha_hash.encode("utf-8")
        return bcrypt.checkpw(senha_bytes, hash_bytes)
    except Exception:
        return False


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


def decodificar_token_acesso(token: str) -> Optional[Dict[str, Any]]:
    """Decodifica o JWT de acesso. Devolve o payload ou None se inválido/expirado.

    Usada por api/deps.py (get_usuario_atual).
    """
    return verificar_token_acesso(token)


# ---------------------------------------------------------------------------
# Token de aprovação de cadastro (link enviado por e-mail ao gestor)
# ---------------------------------------------------------------------------
_SALT_APROVACAO = "aprovacao-usuario"


def _serializer_aprovacao() -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(settings.SECRET_KEY, salt=_SALT_APROVACAO)


def gerar_token_aprovacao(usuario_id: int) -> str:
    """Gera o token assinado usado no link de aprovação enviado ao gestor."""
    return _serializer_aprovacao().dumps({"usuario_id": usuario_id})


def validar_token_aprovacao(token: str, max_horas: int = 48) -> int:
    """Devolve o id do usuário. Levanta ValueError se o token for inválido ou expirado."""
    try:
        dados = _serializer_aprovacao().loads(token, max_age=max_horas * 3600)
    except SignatureExpired:
        raise ValueError("Link de aprovação expirado.")
    except BadSignature:
        raise ValueError("Link de aprovação inválido.")
    return int(dados["usuario_id"])