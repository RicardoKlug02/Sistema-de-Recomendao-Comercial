from typing import Generator
import ssl
from sqlalchemy import create_engine
from sqlalchemy.engine import URL, make_url
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from src.backend.app.core.config import settings


def database_url():
    if settings.DATABASE_URL:
        url = make_url(settings.DATABASE_URL)
        if url.drivername in ("postgres", "postgresql"):
            url = url.set(drivername="postgresql+pg8000")
    else:
        url = URL.create("postgresql+pg8000", username=settings.DB_USER,
                         password=settings.DB_PASSWORD, host=settings.DB_HOST,
                         port=int(settings.DB_PORT), database=settings.DB_NAME)
    if url.drivername == "postgresql+pg8000":
        # Parâmetros libpq não pertencem ao pg8000; TLS é configurado abaixo.
        url = url.set(query={k: v for k, v in url.query.items()
                             if k not in ("sslmode", "channel_binding", "connect_timeout")})
    return url


DATABASE_URL = database_url()
options = {"pool_pre_ping": True, "pool_recycle": 300}
if DATABASE_URL.drivername.startswith("postgresql"):
    options.update(pool_size=settings.DATABASE_POOL_SIZE,
                   max_overflow=settings.DATABASE_MAX_OVERFLOW, pool_timeout=30)
    if DATABASE_URL.drivername == "postgresql+pg8000":
        original_query = make_url(settings.DATABASE_URL).query if settings.DATABASE_URL else {}
        remoto = DATABASE_URL.host not in (None, "localhost", "127.0.0.1", "::1")
        usar_tls = remoto or original_query.get("sslmode") in ("require", "verify-ca", "verify-full")
        options["connect_args"] = {"timeout": int(original_query.get("connect_timeout", 20))}
        if usar_tls:
            options["connect_args"]["ssl_context"] = ssl.create_default_context()
elif DATABASE_URL.drivername == "sqlite":
    options["connect_args"] = {"check_same_thread": False}
engine = create_engine(DATABASE_URL, **options)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
