from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from src.backend.app.core.database import Base 

class Cliente(Base):
    __tablename__ = 'clientes'
    id = Column(Integer, primary_key=True, autoincrement=True)
    razao_social = Column(String(150), nullable=False)
    nome_fantasia = Column(String(150))
    cnpj_cpf = Column(String(18), unique=True)
    cep = Column(String(10))           
    grupo_economico = Column(String(100)) # Mapeado de "Rede de clientes"
    micro_regiao = Column(String(50))
    cidade = Column(String(100))
    estado = Column(String(2))