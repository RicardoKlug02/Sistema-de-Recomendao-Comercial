from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.core.database import Base 

class Fabrica(Base):
    __tablename__ = 'fabricas'
    id = Column(Integer, primary_key=True, autoincrement=True)
    nome_fantasia = Column(String(100), nullable=False)
    cnpj = Column(String(18), unique=True)
    
    # Relações
    produtos = relationship("Produto", back_populates="fabrica")
    vendas = relationship("Venda", back_populates="fabrica")