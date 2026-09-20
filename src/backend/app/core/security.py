from datetime import datetime, timedelta, timezone
import os
from typing import Any, Dict, Optional

import bcrypt
from cryptography.fernet import Fernet, InvalidToken
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
import jwt

import hmac
import hashlib
import re

# --- Chaves e Configurações de Segurança ---
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "CHAVE_SECRETA_RAFAEL_RICARDO_2026")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", str(60 * 8)))

CHAVE_SERIALIZER = os.getenv("CHAVE_SERIALIZER", JWT_SECRET_KEY)
serializer = URLSafeTimedSerializer(CHAVE_SERIALIZER)

# Inicialização resiliente da cifra Fernet
ENCRYPTION_KEY = os.getenv("SECRET_ENCRYPTION_KEY")
try:
    fernet = Fernet(ENCRYPTION_KEY.encode()) if ENCRYPTION_KEY else None
except (ValueError, Exception):
    fernet = None

BLIND_INDEX_SALT = os.getenv("BLIND_INDEX_SALT", "SALT_DETERMINISTICO_2026")

# --- Senhas (Bcrypt) ---

def gerar_hash_senha(senha_plana: str) -> str:
    """Gera o hash seguro bcrypt respeitando o limite do algoritmo (72 bytes)."""
    senha_bytes = senha_plana.encode("utf-8")[:72]
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(senha_bytes, salt).decode("utf-8")


def verificar_senha(senha_plana: str, senha_hash: str) -> bool:
    """Compara a senha em texto plano com o hash gravado."""
    senha_bytes = senha_plana.encode("utf-8")[:72]
    hash_bytes = senha_hash.encode("utf-8")
    return bcrypt.checkpw(senha_bytes, hash_bytes)


# --- Criptografia Simétrica (Fernet / AES) ---

def encrypt_data(plain_text: Optional[str]) -> Optional[str]:
    """Criptografa o texto legível para salvar no banco."""
    if not plain_text or not fernet:
        return plain_text
    return fernet.encrypt(str(plain_text).strip().encode("utf-8")).decode("utf-8")


def decrypt_data(cipher_text: Optional[str]) -> Optional[str]:
    """Descriptografa o dado cifrado em memória para leitura."""
    if not cipher_text or not fernet:
        return cipher_text
    try:
        return fernet.decrypt(str(cipher_text).encode("utf-8")).decode("utf-8")
    except (InvalidToken, Exception):
        return cipher_text  # Fallback caso o dado já esteja em texto puro


# --- Tokens de Sessão (JWT) ---

def criar_token_acesso(
    dados: Dict[str, Any], expira_em: Optional[timedelta] = None
) -> str:
    """Gera um token JWT assinado contendo dados de identificação e perfil."""
    payload = dados.copy()
    agora = datetime.now(timezone.utc)

    if expira_em:
        expiracao = agora + expira_em
    else:
        expiracao = agora + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    payload.update({"exp": expiracao, "iat": agora})
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def decodificar_token_acesso(token: str) -> Optional[Dict[str, Any]]:
    """Decodifica e valida a assinatura e expiração do JWT."""
    try:
        return jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    except jwt.PyJWTError:
        return None


# --- Tokens de Aprovação por E-mail (ItsDangerous) ---

def gerar_token_aprovacao(usuario_id: int) -> str:
    """Gera uma assinatura segura temporal para validação de cadastro via URL."""
    return serializer.dumps(usuario_id, salt="aprovacao-usuario")


def validar_token_aprovacao(token: str, max_horas: int = 48) -> int:
    """Decodifica o token assinado e extrai o ID do usuário liberado."""
    max_idade_segundos = max_horas * 3600
    try:
        usuario_id = serializer.loads(
            token, salt="aprovacao-usuario", max_age=max_idade_segundos
        )
        return int(usuario_id)
    except SignatureExpired:
        raise ValueError("O link de aprovação expirou.")
    except BadSignature:
        raise ValueError("Link de aprovação inválido ou corrompido.")

def gerar_blind_index(documento: Optional[str]) -> Optional[str]:
    """Gera um hash HMAC-SHA256 determinístico para busca exata O(1)."""
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