from logging.config import fileConfig
from alembic import context
from src.backend.app.core.database import Base, engine
from src.backend.app import models

config = context.config
if config.config_file_name:
    fileConfig(config.config_file_name)
target_metadata = Base.metadata


def offline():
    context.configure(url=engine.url.render_as_string(hide_password=False),
                      target_metadata=target_metadata, literal_binds=True, compare_type=True)
    with context.begin_transaction():
        context.run_migrations()


def migrar(connection):
    context.configure(connection=connection, target_metadata=target_metadata, compare_type=True)
    with context.begin_transaction():
        context.run_migrations()


def online():
    connection = config.attributes.get("connection")
    if connection is not None:
        migrar(connection)
    else:
        with engine.connect() as connection:
            migrar(connection)


offline() if context.is_offline_mode() else online()
