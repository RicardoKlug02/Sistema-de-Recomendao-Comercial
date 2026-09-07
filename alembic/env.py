import os
import sys
from pathlib import Path
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# 2. Imporamos a Base, engine e modelos para gerenciar
from src.backend.app.core.database import Base, engine
import src.backend.app.models  #Garante que todos os models sejam carregados

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 3. Informa os metadados das tabelas ao Alembic3
target_metadata = Base.metadata

def run_migrations_offline() -> None:
    url = str(engine.url)
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    # Usa a própria engine já configurada no database.py
    with engine.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,  # Importante: detecta mudanças no tamanho das colunas (VARCHAR(18) -> VARCHAR(64))
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()