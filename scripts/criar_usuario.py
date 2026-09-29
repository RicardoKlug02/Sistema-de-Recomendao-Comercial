"""Cria o primeiro administrador; solicita a senha sem exibi-la."""

import argparse
from getpass import getpass
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.backend.app.core.database import SessionLocal
from src.backend.app.services.auth_service import AuthService

<<<<<<< Updated upstream
from src.backend.app.core.database import SessionLocal
from src.backend.app.core.security import gerar_hash_senha
from src.backend.app.models.usuario import Usuario

EMAIL_ADMIN = "rick.nklug@gmail.com"
NOME_ADMIN = "Ricardo Klug"
SENHA_ADMIN = "Ricklegal55."  

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
=======

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--email", required=True)
    parser.add_argument("--nome", required=True)
    args = parser.parse_args()
    from pydantic import TypeAdapter, EmailStr

    email = str(TypeAdapter(EmailStr).validate_python(args.email))
    senha = getpass("Senha do administrador (mínimo 10 caracteres): ")
    if len(senha) < 10 or len(senha.encode()) > 72:
        raise SystemExit("Senha fora do limite de 10 caracteres a 72 bytes.")
    if senha != getpass("Confirme a senha: "):
        raise SystemExit("Senhas diferentes.")
    with SessionLocal() as db:
        servico = AuthService(db)
        if servico.buscar_por_email(email):
            raise SystemExit("E-mail já cadastrado; acesso existente não foi alterado.")
        u = servico.criar_usuario(args.nome, email, senha, perfil="admin")
        servico.aprovar_usuario(u.id)
    print("Administrador criado e aprovado.")


if __name__ == "__main__":
    main()
>>>>>>> Stashed changes
