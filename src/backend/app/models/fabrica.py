from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from src.backend.app.core.database import Base


class Fabrica(Base):
    __tablename__ = "fabricas"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nome_fantasia = Column(String(100), nullable=False, index=True)
    cnpj = Column(String(18), unique=True, index=True)

    # Relações
    produtos = relationship("Produto", back_populates="fabrica", cascade="all, delete-orphan")
    vendas = relationship("Venda", back_populates="fabrica")

    def __repr__(self):
        return f"<Fabrica id={self.id} nome='{self.nome_fantasia}'>"