from sqlalchemy import Column, Index, Integer, String
from sqlalchemy.orm import relationship

from src.backend.app.core.database import Base
from src.backend.app.core.types import EncryptedString


class Cliente(Base):
    __tablename__ = "clientes"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Campos protegidos por criptografia simétrica em repouso
    razao_social = Column(EncryptedString(512), nullable=False)
    nome_fantasia = Column(EncryptedString(512), nullable=True)

    # Documento armazenado (pode ser cifrado ou o token anonimizado CLI_...)
    cnpj_cpf = Column(EncryptedString(512), nullable=True)

    # Blind Index: Hash determinístico com salt seguro para busca exata O(1)
    cnpj_hash = Column(String(64), unique=True, index=True, nullable=True)

    # Localização e aglutinação comercial
    cep = Column(String(10), nullable=True)
    grupo_economico = Column(String(100), index=True, nullable=True)
    micro_regiao = Column(String(50), index=True, nullable=True)
    cidade = Column(String(100), nullable=True)
    estado = Column(String(2), nullable=True)

    # Relacionamento com Vendas
    vendas = relationship(
        "Venda",
        back_populates="cliente",
        cascade="all, delete-orphan",
        lazy="select",
    )

    def __repr__(self) -> str:
        return f"<Cliente id={self.id} grupo_economico='{self.grupo_economico}'>"