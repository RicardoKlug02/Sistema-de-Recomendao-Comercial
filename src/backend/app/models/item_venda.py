from decimal import Decimal
from sqlalchemy import Column, Integer, Numeric, ForeignKey
from sqlalchemy.orm import relationship
from src.backend.app.core.database import Base


class ItemVenda(Base):
    __tablename__ = "itens_venda"

    id = Column(Integer, primary_key=True, autoincrement=True)
    venda_id = Column(
        Integer, ForeignKey("vendas.id", ondelete="CASCADE"), nullable=False, index=True
    )
    produto_id = Column(Integer, ForeignKey("produtos.id"), nullable=False, index=True)
    quantidade = Column(Integer, nullable=False, default=1)
    preco_unitario = Column(Numeric(16, 2), nullable=False)

    subtotal = Column(
        Numeric(16, 2),
        nullable=False,
        default=lambda ctx: Decimal(str(ctx.get_current_parameters()["preco_unitario"]))
        * ctx.get_current_parameters()["quantidade"],
    )

    # Relações bidirecionais
    venda = relationship("Venda", back_populates="itens")
    produto = relationship("Produto", back_populates="itens_venda")

    def __repr__(self):
        return f"<ItemVenda id={self.id} venda_id={self.venda_id} produto_id={self.produto_id}>"
