from sqlalchemy import Column, Integer, Float, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base 

class ItemVenda(Base):
    __tablename__ = 'itens_venda'
    id = Column(Integer, primary_key=True, autoincrement=True)
    venda_id = Column(Integer, ForeignKey('vendas.id'))
    produto_id = Column(Integer, ForeignKey('produtos.id'))
    quantidade = Column(Integer, nullable=False)
    preco_unitario = Column(Float, nullable=False)

    venda = relationship("Venda", back_populates="itens")