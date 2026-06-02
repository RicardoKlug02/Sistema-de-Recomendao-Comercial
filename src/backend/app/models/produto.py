from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from src.backend.app.core.database import Base 

class Produto(Base):
    __tablename__ = 'produtos'
    id = Column(Integer, primary_key=True, autoincrement=True)
    fabrica_id = Column(Integer, ForeignKey('fabricas.id'))
    nome = Column(String(150), nullable=False)
    sku = Column(String(50), unique=True)
    
    fabrica = relationship("Fabrica", back_populates="produtos")