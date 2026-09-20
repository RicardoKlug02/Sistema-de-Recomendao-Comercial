import sys
from pathlib import Path
from unittest.mock import AsyncMock, patch
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.backend.app.core.database import Base, get_db
from src.backend.main import app
from src.backend.app.models.usuario import Usuario
from src.backend.app.core.security import gerar_hash_senha

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(autouse=True)
def mock_email_service():
    """Intercepta chamadas de e-mail automaticamente em todos os testes."""
    with patch("fastapi_mail.FastMail.send_message", new_callable=AsyncMock) as mock_mail:
        yield mock_mail


@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def usuario_admin(db_session):
    user = Usuario(
        nome="Admin Tester",
        email="admin@teste.com",
        senha_hash=gerar_hash_senha("admin123"),
        perfil="admin",
        aprovado=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def token_admin(client, usuario_admin):
    res = client.post(
        "/api/v1/auth/login",
        data={"username": "admin@teste.com", "password": "admin123"},
    )
    assert res.status_code == 200, f"Falha no login do admin: {res.text}"
    return res.json()["access_token"]