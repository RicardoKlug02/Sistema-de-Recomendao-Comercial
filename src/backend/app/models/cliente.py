from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from src.backend.app.core.database import Base 

class Cliente(Base):
    __tablename__ = 'clientes'
    id = Column(Integer, primary_key=True, autoincrement=True)
    razao_social = Column(String(255), nullable=False)
    nome_fantasia = Column(String(255))
    cnpj_cpf = Column(String(64), unique=True)
    cep = Column(String(10))           
    grupo_economico = Column(String(100))
    micro_regiao = Column(String(50))
    cidade = Column(String(100))
    estado = Column(String(2))