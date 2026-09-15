import os
import sys
from pathlib import Path
from logging.config import fileConfig
from alembic import context

# 1. Garante a raiz do projeto no sys.path
BASE_DIR = Path(__file__).resolve().parents[1]
while BASE_DIR.name != "src" and BASE_DIR.parent != BASE_DIR:
    if (BASE_DIR / "src").exists() or (BASE_DIR / ".env").exists():
        break
    BASE_DIR = BASE_DIR.parent

if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# 2. Configurações de log do Alembic
config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 3. Importação da Base, Engine e Models
from src.backend.app.core.database import Base, engine

# Import direto para garantir registro absoluto no Base.metadata
from src.backend.app.models.cliente import Cliente
from src.backend.app.models.fabrica import Fabrica
from src.backend.app.models.item_venda import ItemVenda
from src.backend.app.models.produto import Produto
from src.backend.app.models.usuario import Usuario
from src.backend.app.models.venda import Venda
from src.backend.app.models.vendedor import Vendedor

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
    with engine.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()