"""Reset explícito apenas das tabelas do projeto. Não executado no startup."""
import argparse
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--confirmar", action="store_true")
    parser.add_argument("--host", required=True, help="Hostname esperado do banco (sem senha)")
    args = parser.parse_args()
    from src.backend.app.core.database import Base, engine
    from src.backend.app import models
    from sqlalchemy import text
    if not args.confirmar or engine.url.host != args.host:
        raise SystemExit("Reset cancelado: confirme explicitamente e informe o host exato configurado.")
    from src.backend.app.core.config import settings
    if not settings.ADMIN_PASSWORD or len(settings.ADMIN_PASSWORD.encode()) < 8:
        raise SystemExit("Reset cancelado: configure ADMIN_PASSWORD com pelo menos 8 bytes para o administrador inicial.")
    with engine.begin() as connection:
        Base.metadata.drop_all(connection)
        connection.execute(text("DROP TABLE IF EXISTS alembic_version"))
    from start import run_migrations, bootstrap_admin
    run_migrations()
    bootstrap_admin()
    print("Tabelas do projeto reconstruídas. Nenhuma planilha foi importada automaticamente.")


if __name__ == "__main__":
    main()
