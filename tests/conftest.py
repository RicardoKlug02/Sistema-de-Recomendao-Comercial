import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.backend.app.models import Base

@pytest.fixture
def session():
    # Cria um banco SQLite em memória apenas para a execução dos testes
    engine = create_engine("sqlite:///:memory:")
    
    # Se tiver a Base declarativa, descomente a linha abaixo para gerar o schema:
    # Base.metadata.create_all(bind=engine)
    
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()
    
    try:
        yield db
    finally:
        db.close()