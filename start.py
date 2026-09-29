"""Render: migrações verificadas, administrador inicial e API na porta PORT."""
import os
from pathlib import Path
import uvicorn
from alembic import command
from alembic.config import Config


def run_migrations():
    config = Config(str(Path(__file__).parent / "alembic.ini"))
    command.upgrade(config, "head")


def bootstrap_admin():
    from src.backend.app.core.config import settings
    from src.backend.app.core.database import SessionLocal
    from src.backend.app.core.security import gerar_hash_senha
    from src.backend.app.models import Usuario
    if not settings.ADMIN_PASSWORD:
        return
    if len(settings.ADMIN_PASSWORD.encode()) < 8:
        raise ValueError("ADMIN_PASSWORD deve ter pelo menos 8 bytes.")
    with SessionLocal() as db:
        email = settings.ADMIN_EMAIL.strip().lower()
        if not db.query(Usuario).filter_by(email=email).first():
            db.add(Usuario(nome=settings.ADMIN_NAME, email=email,
                           senha_hash=gerar_hash_senha(settings.ADMIN_PASSWORD),
                           perfil="admin", ativo=True, aprovado=True))
            db.commit()


if __name__ == "__main__":
    run_migrations()  # Falha interrompe o deploy; nunca marca revisões não executadas.
    bootstrap_admin()
    uvicorn.run("src.backend.main:app", host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
