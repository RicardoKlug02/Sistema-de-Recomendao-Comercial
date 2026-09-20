from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, Integer, String
from src.backend.app.core.database import Base
from datetime import datetime, timezone

class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(150), nullable=False)
    email = Column(String(150), unique=True, index=True, nullable=False)
    senha_hash = Column(String(255), nullable=False)
    perfil = Column(String(50), default="vendedor", nullable=False)  # 'admin', 'vendedor'
    ativo = Column(Boolean, default=True, nullable=False)
    aprovado = Column(Boolean, default=False, nullable=False)  # Liberado via link de aprovação
    criado_em = Column(DateTime, default=datetime.now(timezone.utc), nullable=False)

    def __repr__(self):
        return f"<Usuario id={self.id} email='{self.email}' perfil='{self.perfil}'>"