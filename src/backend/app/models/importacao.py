from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, Integer, String, Text
from src.backend.app.core.database import Base


class Importacao(Base):
    __tablename__ = "importacoes"
    id = Column(Integer, primary_key=True)
    arquivo = Column(String(255), nullable=False)
    arquivo_itens = Column(String(255), nullable=False)
    usuario = Column(String(150), nullable=False)
    criado_em = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    processados = Column(Integer, nullable=False, default=0)
    adicionados = Column(Integer, nullable=False, default=0)
    atualizados = Column(Integer, nullable=False, default=0)
    itens = Column(Integer, nullable=False, default=0)
    pedidos_sem_itens = Column(Integer, nullable=False, default=0)
    avisos_json = Column(Text, nullable=False, default="[]")
