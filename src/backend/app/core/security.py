import hashlib
import hmac
import os
import re
import bcrypt
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from cryptography.fernet import Fernet
from jose import JWTError, jwt
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from src.backend.app.core.config import settings

<<<<<<< Updated upstream
FERNET_CIPHER = Fernet(settings.SECRET_ENCRYPTION_KEY.encode("utf-8"))
BLIND_INDEX_SALT = getattr(settings, "BLIND_INDEX_SALT", settings.SECRET_KEY)


def gerar_hash_senha(senha: str) -> str:
    """Gera hash bcrypt com salt automático."""
    # Trunca em 72 bytes por especificação do algoritmo bcrypt
    senha_bytes = senha.encode("utf-8")[:72]
=======
from src.backend.app.core.config import settings

JWT_SECRET_KEY = settings.JWT_SECRET_KEY
JWT_ALGORITHM = settings.JWT_ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES
serializer = URLSafeTimedSerializer(settings.CHAVE_SERIALIZER)
fernet = Fernet(settings.SECRET_ENCRYPTION_KEY.encode())
BLIND_INDEX_SALT = settings.BLIND_INDEX_SALT

# --- Senhas (Bcrypt) ---


def gerar_hash_senha(senha_plana: str) -> str:
    """Gera o hash seguro bcrypt respeitando o limite do algoritmo (72 bytes)."""
    senha_bytes = senha_plana.encode("utf-8")
    if len(senha_bytes) > 72:
        raise ValueError("A senha deve ter até 72 bytes.")
>>>>>>> Stashed changes
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(senha_bytes, salt).decode("utf-8")


def verificar_senha(senha_plana: str, senha_hash: str) -> bool:
<<<<<<< Updated upstream
    """Verifica se a senha em texto plano bate com o hash armazenado."""
    try:
        senha_bytes = senha_plana.encode("utf-8")[:72]
        hash_bytes = senha_hash.encode("utf-8")
        return bcrypt.checkpw(senha_bytes, hash_bytes)
    except Exception:
        return False


def encriptar_dado(dado: Optional[str]) -> Optional[str]:
    if not dado:
=======
    """Compara a senha em texto plano com o hash gravado."""
    senha_bytes = senha_plana.encode("utf-8")
    if len(senha_bytes) > 72:
        return False
    hash_bytes = senha_hash.encode("utf-8")
    return bcrypt.checkpw(senha_bytes, hash_bytes)


# --- Criptografia Simétrica (Fernet / AES) ---


def encrypt_data(plain_text: Optional[str]) -> Optional[str]:
    """Criptografa o texto legível para salvar no banco."""
    if not plain_text:
        return plain_text
    return fernet.encrypt(str(plain_text).strip().encode("utf-8")).decode("utf-8")


def decrypt_data(cipher_text: Optional[str]) -> Optional[str]:
    """Descriptografa o dado cifrado em memória para leitura."""
    if not cipher_text:
        return cipher_text
    try:
        return fernet.decrypt(str(cipher_text).encode("utf-8")).decode("utf-8")
    except InvalidToken:
        if str(cipher_text).startswith("gAAAA"):
            raise ValueError("Não foi possível decifrar o registro; verifique a chave.")
        return cipher_text  # Compatibilidade de leitura com registros legados; novas escritas sempre cifradas.


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
>>>>>>> Stashed changes
        return None
    return FERNET_CIPHER.encrypt(str(dado).encode("utf-8")).decode("utf-8")


<<<<<<< Updated upstream
def decriptar_dado(dado_cifrado: Optional[str]) -> Optional[str]:
    if not dado_cifrado:
        return None
=======
# --- Tokens de Aprovação por E-mail (ItsDangerous) ---


def gerar_token_aprovacao(usuario_id: int) -> str:
    """Gera uma assinatura segura temporal para validação de cadastro via URL."""
    return serializer.dumps(usuario_id, salt="aprovacao-usuario")


def validar_token_aprovacao(token: str, max_horas: int = 48) -> int:
    """Decodifica o token assinado e extrai o ID do usuário liberado."""
    max_idade_segundos = max_horas * 3600
>>>>>>> Stashed changes
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
<<<<<<< Updated upstream


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


def gerar_token_aprovacao(usuario_id: int) -> str:
    """Assina um identificador exclusivo para aprovação, separado do token de login."""
    return URLSafeTimedSerializer(settings.CHAVE_SERIALIZER).dumps(
        usuario_id, salt="aprovacao-usuario"
    )


def validar_token_aprovacao(token: str, max_horas: int = 48) -> int:
    """Recusa links adulterados, expirados ou com conteúdo inválido."""
    try:
        usuario_id = URLSafeTimedSerializer(settings.CHAVE_SERIALIZER).loads(
            token, salt="aprovacao-usuario", max_age=max_horas * 3600
        )
        if type(usuario_id) is not int or usuario_id <= 0:
            raise ValueError("Token inválido ou corrompido.")
        return usuario_id
    except SignatureExpired as erro:
        raise ValueError("Link de aprovação expirado. Solicite um novo envio.") from erro
    except BadSignature as erro:
        raise ValueError("Token inválido ou corrompido.") from erro


# Compatibilidade com os consumidores existentes, sem duplicar implementações.
decodificar_token_acesso = verificar_token_acesso
encrypt_data = encriptar_dado
decrypt_data = decriptar_dado
=======
>>>>>>> Stashed changes
