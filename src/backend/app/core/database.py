from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker
from src.backend.app.core.config import settings

opcoes = {"pool_pre_ping": True}
if settings.DATABASE_URL.startswith("sqlite"):
    opcoes["connect_args"] = {"check_same_thread": False}
else:
    opcoes.update(pool_size=10, max_overflow=20, pool_recycle=1800)
engine = create_engine(settings.DATABASE_URL, **opcoes)
if engine.dialect.name == "sqlite":

    @event.listens_for(engine, "connect")
    def sqlite_foreign_keys(connection, _):
        connection.execute("PRAGMA foreign_keys=ON")


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    with SessionLocal() as db:
        yield db
