from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.core.database import Base 

class Cliente(Base):
    __tablename__ = 'clientes'
    id = Column(Integer, primary_key=True, autoincrement=True)
    # ... resto dos atributos