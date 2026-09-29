from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, Text
from src.backend.app.core.database import Base


class Importacao(Base):
    __tablename__ = "importacoes"
    id = Column(Integer, primary_key=True)
    arquivos = Column(String(512), nullable=False)
    usuario = Column(String(150), nullable=False)
    status = Column(String(30), nullable=False)
    mensagem = Column(Text, nullable=False)
    criado_em = Column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
