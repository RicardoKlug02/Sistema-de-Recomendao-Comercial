import sys
from pathlib import Path

raiz = Path(__file__).resolve().parent.parent
if str(raiz) not in sys.path:
    sys.path.insert(0, str(raiz))

from src.backend.app.core.database import SessionLocal
from src.backend.app.core.security import gerar_hash_senha
from src.backend.app.models.usuario import Usuario

import os
from getpass import getpass

EMAIL_ADMIN = os.getenv("ADMIN_EMAIL") or input("E-mail do admin: ")
SENHA_ADMIN = os.getenv("ADMIN_SENHA") or getpass("Senha do admin: ")

with SessionLocal() as session:
    usuario_existente = session.query(Usuario).filter(Usuario.email == EMAIL_ADMIN).first()

    if usuario_existente:
        print(f"Usuário {EMAIL_ADMIN} já existe no banco (ID: {usuario_existente.id}) | Perfil: {usuario_existente.perfil} | Aprovado: {usuario_existente.aprovado}")
    else:
        novo_admin = Usuario(
            nome=NOME_ADMIN,
            email=EMAIL_ADMIN,
            senha_hash=gerar_hash_senha(SENHA_ADMIN),
            perfil="admin",
            aprovado=True,
        )
        session.add(novo_admin)
        session.commit()
        session.refresh(novo_admin)

        print(f"Administrador criado com sucesso!")
        print(f"ID: {novo_admin.id} | Nome: {novo_admin.nome} | Email: {novo_admin.email} | Perfil: {novo_admin.perfil}")