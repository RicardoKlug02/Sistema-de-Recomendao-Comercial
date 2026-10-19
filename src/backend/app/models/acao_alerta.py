from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, Date, DateTime, ForeignKey, CheckConstraint
from src.backend.app.core.database import Base


class AcaoAlerta(Base):
    """Eventos de acompanhamento compartilhados pela equipe; não apagam o sinal analítico."""
    __tablename__ = 'acoes_alerta'
    __table_args__ = (CheckConstraint("situacao IN ('PENDENTE','CONTATADO','AGUARDANDO_RETORNO','DISPENSADO')", name='ck_acao_alerta_situacao'),)
    id = Column(Integer, primary_key=True)
    cliente_id = Column(Integer, ForeignKey('clientes.id'), nullable=False, index=True)
    usuario_id = Column(Integer, ForeignKey('usuarios.id'), nullable=False)
    assinatura = Column(String(64), nullable=False)
    situacao = Column(String(30), nullable=False)
    motivo = Column(Text, nullable=False, default='')
    proximo_contato = Column(Date, nullable=True)
    criado_em = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
