"""Valida as migrações em um esquema temporário sem tocar nas tabelas públicas."""
import sys
import uuid
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def main():
    from sqlalchemy import text, inspect
    from alembic import command
    from alembic.config import Config
    from src.backend.app.core.database import engine
    esquema = "codex_check_" + uuid.uuid4().hex
    with engine.connect() as connection:
        # DDL transacional: o esquema e todos os objetos são descartados por rollback.
        transaction = connection.begin()
        try:
            connection.execute(text(f'CREATE SCHEMA "{esquema}"'))
            connection.execute(text(f'SET LOCAL search_path TO "{esquema}"'))
            config = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
            config.attributes["connection"] = connection
            command.upgrade(config, "head")
            tabelas = inspect(connection).get_table_names(schema=esquema)
            assert all(n in tabelas for n in ("clientes", "vendas", "itens_venda", "importacoes", "usuarios"))
            revisao = connection.execute(text("SELECT version_num FROM alembic_version")).scalar()
            assert revisao == "20260929_operacao"
            print("Migrações verificadas em PostgreSQL: criação completa e revisão final corretas.")
        finally:
            transaction.rollback()
    print("Esquema temporário removido por rollback. Tabelas públicas preservadas.")


if __name__ == "__main__":
    main()
