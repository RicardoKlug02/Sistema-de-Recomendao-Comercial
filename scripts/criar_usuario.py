import sys
from pathlib import Path
from getpass import getpass
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def main():
    from src.backend.app.core.database import SessionLocal
    from src.backend.app.core.security import gerar_hash_senha
    from src.backend.app.models import Usuario
    nome = input("Nome do administrador: ").strip()
    email = input("E-mail do administrador: ").strip().lower()
    senha = getpass("Senha (mínimo 8 caracteres): ")
    if not nome or "@" not in email or len(senha) < 8:
        raise ValueError("Informe nome, e-mail e senha válidos.")
    with SessionLocal() as db:
        if db.query(Usuario).filter_by(email=email).first():
            raise ValueError("E-mail já cadastrado. Nenhuma alteração realizada.")
        db.add(Usuario(nome=nome, email=email, senha_hash=gerar_hash_senha(senha),
                       perfil="admin", ativo=True, aprovado=True))
        db.commit()
    print("Administrador criado.")


if __name__ == "__main__":
    main()
