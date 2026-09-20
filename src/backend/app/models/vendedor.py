from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from src.backend.app.core.database import Base


class Vendedor(Base):
    __tablename__ = "vendedores"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String(100), nullable=False, index=True)

    # Relação com vendas
    vendas = relationship("Venda", backref="vendedor")

    def __repr__(self):
        return f"<Vendedor id={self.id} nome='{self.nome}'>"