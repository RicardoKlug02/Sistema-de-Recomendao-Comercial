from sqlalchemy import Column, Integer, Float, ForeignKey, Date, String
from sqlalchemy.orm import relationship
from src.backend.app.core.database import Base


class Venda(Base):
    __tablename__ = "vendas"

    id = Column(Integer, primary_key=True, autoincrement=True)
    numero_pedido = Column(String(50), unique=True, index=True)
    cliente_id = Column(Integer, ForeignKey("clientes.id", ondelete="CASCADE"), nullable=False, index=True)
    vendedor_id = Column(Integer, ForeignKey("vendedores.id"), nullable=True, index=True)
    fabrica_id = Column(Integer, ForeignKey("fabricas.id"), nullable=False, index=True)
    data_venda = Column(Date, nullable=False, index=True)  # Indexado para filtros de datas rápidos
    valor_total = Column(Float, default=0.0, nullable=False)

    # Relações
    cliente = relationship("Cliente", back_populates="vendas")
    fabrica = relationship("Fabrica", back_populates="vendas")
    itens = relationship("ItemVenda", back_populates="venda", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Venda id={self.id} pedido='{self.numero_pedido}' total={self.valor_total}>"