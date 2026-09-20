from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from src.backend.app.core.database import Base


class Produto(Base):
    __tablename__ = "produtos"

    id = Column(Integer, primary_key=True, autoincrement=True)
    fabrica_id = Column(Integer, ForeignKey("fabricas.id", ondelete="RESTRICT"), nullable=False, index=True)
    nome = Column(String(255), nullable=False, index=True)
    sku = Column(String(150), unique=True, index=True)

    # Relações bidirecionais
    fabrica = relationship("Fabrica", back_populates="produtos")
    itens_venda = relationship("ItemVenda", back_populates="produto")

    def __repr__(self):
        return f"<Produto id={self.id} nome='{self.nome}' sku='{self.sku}'>"