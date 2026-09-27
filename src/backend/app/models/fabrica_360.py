from sqlalchemy import Column, Float, Integer, String, Text
from src.backend.app.core.database import Base


class FabricaAnalytics(Base):
    __tablename__ = "fabrica_analytics"

    id = Column(Integer, primary_key=True, index=True)
    fabrica_id = Column(Integer, index=True)
    regiao_imediata = Column(String(100), index=True, nullable=True)
    
    total_vendas = Column(Float, default=0.0)
    volume_vendido = Column(Float, default=0.0)
    tendencia_venda = Column(String(20), nullable=True) # "ALTA", "QUEDA", "ESTAVEL"
    
    top_produtos_json = Column(Text, nullable=True) # Top 10 produtos mais vendidos da fábrica