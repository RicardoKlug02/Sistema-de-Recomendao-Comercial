from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.core.database import Base 

class Vendedores(Base):
    __tablename__ = 'vendedores'
    id = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String(100), nullable=False)