"""Gera .env local uma única vez; não sobrescreve configurações existentes."""

from pathlib import Path
import secrets
from cryptography.fernet import Fernet

raiz = Path(__file__).resolve().parents[1]
conteudo = (raiz / ".env.example").read_text()
for nome in ["JWT_SECRET_KEY", "CHAVE_SERIALIZER", "BLIND_INDEX_SALT"]:
    conteudo = conteudo.replace(f"{nome}=GERAR", f"{nome}={secrets.token_urlsafe(48)}")
conteudo = conteudo.replace(
    "SECRET_ENCRYPTION_KEY=GERAR",
    "SECRET_ENCRYPTION_KEY=" + Fernet.generate_key().decode(),
)
try:
    with (raiz / ".env").open("x") as arq:
        arq.write(conteudo)
    (raiz / ".env").chmod(0o600)
    print("Configuração local criada. Preserve as chaves em backup seguro.")
except FileExistsError:
    print(".env já existe; nenhuma configuração foi alterada.")
