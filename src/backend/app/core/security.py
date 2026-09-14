import os
from cryptography.fernet import Fernet
import bcrypt
from datetime import datetime, timedelta, timezone
from typing import Optional
import jwt

ENCRYPTION_KEY = os.getenv("SECRET_ENCRYPTION_KEY")
# Garante fallback durante desenvolvimento inicial
fernet = Fernet(ENCRYPTION_KEY.encode()) if ENCRYPTION_KEY else None

def gerar_hash_senha(senha_plana: str) -> str:
    """Gera o hash seguro bcrypt para persistência no banco."""
    # Garante o limite de 72 bytes do algoritmo bcrypt
    senha_bytes = senha_plana.encode("utf-8")[:72]
    salt = bcrypt.gensalt()
    hash_bytes = bcrypt.hashpw(senha_bytes, salt)
    return hash_bytes.decode("utf-8")


def verificar_senha(senha_plana: str, senha_hash: str) -> bool:
    """Compara a senha informada no login com o hash gravado."""
    senha_bytes = senha_plana.encode("utf-8")[:72]
    hash_bytes = senha_hash.encode("utf-8")
    return bcrypt.checkpw(senha_bytes, hash_bytes)

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

    # Pode mover estas constantes para o seu settings/core/config.py se já tiver
JWT_SECRET_KEY = (
    "CHAVE_SECRETA_RAFAEL_RICARDO_2026"  # Troque ou puxe do seu .env
)
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 8  # 8 horas de expediente comercial


def criar_token_acesso(
    dados: dict, expira_em: Optional[timedelta] = None
) -> str:
    """Gera um token JWT assinado com tempo de expiração."""
    payload = dados.copy()
    agora = datetime.now(timezone.utc)

    if expira_em:
        expiracao = agora + expira_em
    else:
        expiracao = agora + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    payload.update({"exp": expiracao, "iat": agora})
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def decodificar_token_acesso(token: str) -> Optional[dict]:
    """Decodifica e valida assinatura e expiração do JWT."""
    try:
        payload = jwt.decode(
            token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM]
        )
        return payload
    except jwt.PyJWTError:
        return None

from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

# Chave secreta para assinatura dos links (pode ser a mesma do JWT ou do .env)
CHAVE_SERIALIZER = "CHAVE_SECRETA_RAFAEL_RICARDO_26"
serializer = URLSafeTimedSerializer(CHAVE_SERIALIZER)


def gerar_token_aprovacao(usuario_id: int) -> str:
    """Gera uma string segura para ser passada na URL do e-mail."""
    return serializer.dumps(usuario_id, salt="aprovacao-usuario")


def validar_token_aprovacao(token: str, max_horas: int = 48) -> int:
    """Decodifica o link, valida a assinatura e checa se não expirou.

    Retorna o ID do usuário ou levanta erro.
    """
    max_idade_segundos = max_horas * 3600
    try:
        usuario_id = serializer.loads(
            token, salt="aprovacao-usuario", max_age=max_idade_segundos
        )
        return int(usuario_id)
    except SignatureExpired:
        raise ValueError("O link de aprovação expirou.")
    except BadSignature:
        raise ValueError("Link de aprovação inválido ou adulterado.")