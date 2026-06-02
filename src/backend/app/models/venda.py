from sqlalchemy import Column, Integer, Float, ForeignKey, Date
from sqlalchemy.orm import relationship
from src.backend.app.core.database import Base 

class Venda(Base):
    __tablename__ = 'vendas'
    id = Column(Integer, primary_key=True, autoincrement=True)
    cliente_id = Column(Integer, ForeignKey('clientes.id'))
    vendedor_id = Column(Integer, ForeignKey('vendedores.id'))
    fabrica_id = Column(Integer, ForeignKey('fabricas.id'))
    data_venda = Column(Date, nullable=False)
    valor_total = Column(Float)

    fabrica = relationship("Fabrica", back_populates="vendas")
    itens = relationship("ItemVenda", back_populates="venda")