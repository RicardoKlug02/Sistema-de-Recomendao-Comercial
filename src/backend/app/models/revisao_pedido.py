from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from src.backend.app.core.database import Base


class RevisaoPedido(Base):
    """Decisões sobre pedidos, preservadas inclusive se uma sincronização remover a venda."""
    __tablename__ = 'revisoes_pedido'
    id = Column(Integer, primary_key=True)
    venda_id = Column(Integer, ForeignKey('vendas.id', ondelete='SET NULL'), nullable=True, index=True)
    usuario_id = Column(Integer, ForeignKey('usuarios.id'), nullable=True)
    classificacao_anterior = Column(String(30), nullable=False)
    classificacao = Column(String(30), nullable=False)
    motivo = Column(Text, nullable=False)
    evidencia = Column(Text, nullable=False, default='')
    pedido_original = Column(Text, nullable=False)
    criado_em = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
