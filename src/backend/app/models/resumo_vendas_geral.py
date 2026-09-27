from sqlalchemy import Column, Date, Float, Integer, String
from src.backend.app.core.database import Base


class ResumoVendasGeral(Base):
    __tablename__ = "resumo_vendas_geral"

    id = Column(Integer, primary_key=True, index=True)
    ano_mes = Column(String(7), index=True)  # Formato "YYYY-MM"
    regiao_imediata = Column(String(100), index=True, nullable=True)
    vendedor_id = Column(Integer, index=True, nullable=True)
    fabrica_id = Column(Integer, index=True, nullable=True)
    
    total_vendas = Column(Float, default=0.0)
    quantidade_pedidos = Column(Integer, default=0)
    ticket_medio = Column(Float, default=0.0)