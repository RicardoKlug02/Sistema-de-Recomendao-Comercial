from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, Date, DateTime, ForeignKey, CheckConstraint, Text, JSON
from src.backend.app.core.database import Base


class RegraNegocio(Base):
    __tablename__ = 'regras_negocio'
    __table_args__ = (
        CheckConstraint("tipo IN ('SUBSTITUICAO', 'RESTRICAO')", name='ck_regra_tipo'),
        CheckConstraint('fim IS NULL OR fim >= inicio', name='ck_regra_vigencia'),
        CheckConstraint("(tipo = 'SUBSTITUICAO' AND produto_origem_id IS NOT NULL AND produto_destino_id IS NOT NULL AND produto_origem_id <> produto_destino_id AND uf IS NULL) OR (tipo = 'RESTRICAO' AND produto_origem_id IS NULL AND produto_destino_id IS NULL)", name='ck_regra_produtos'),
    )
    id = Column(Integer, primary_key=True)
    tipo = Column(String(20), nullable=False)
    fabrica_id = Column(Integer, ForeignKey('fabricas.id'), nullable=False, index=True)
    cliente_id = Column(Integer, ForeignKey('clientes.id'), nullable=True)
    uf = Column(String(2), nullable=True)
    produto_origem_id = Column(Integer, ForeignKey('produtos.id'), nullable=True)
    produto_destino_id = Column(Integer, ForeignKey('produtos.id'), nullable=True)
    unificar_historico = Column(Boolean, nullable=False, default=True, server_default='true')
    excecoes_clientes = Column(JSON, nullable=False, default=list)
    excecoes_vendedores = Column(JSON, nullable=False, default=list)
    inicio = Column(Date, nullable=False)
    fim = Column(Date, nullable=True)
    ativa = Column(Boolean, nullable=False, default=True)
    motivo = Column(Text, nullable=False, default='')
    criado_por = Column(Integer, ForeignKey('usuarios.id'), nullable=True)
    atualizado_por = Column(Integer, ForeignKey('usuarios.id'), nullable=True)
    criado_em = Column(DateTime(timezone=True), nullable=False, default=lambda:datetime.now(timezone.utc))
    atualizado_em = Column(DateTime(timezone=True), nullable=False, default=lambda:datetime.now(timezone.utc), onupdate=lambda:datetime.now(timezone.utc))
