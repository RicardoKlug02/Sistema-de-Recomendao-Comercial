from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, Text
from src.backend.app.core.database import Base

class ResumoVendasGeral(Base):
    __tablename__ = "resumo_vendas_geral"
    id = Column(Integer, primary_key=True, index=True)
    ano_mes = Column(String(7), index=True)
    regiao_imediata = Column(String(100), index=True)
    vendedor_id = Column(Integer, nullable=True)
    fabrica_id = Column(Integer, nullable=True)
    total_vendas = Column(Float, default=0.0)
    quantidade_pedidos = Column(Integer, default=0)
    ticket_medio = Column(Float, default=0.0)

class ClienteAnalytics(Base):
    __tablename__ = "cliente_analytics"
    id = Column(Integer, primary_key=True, index=True)
    cliente_id = Column(Integer, ForeignKey("clientes.id"), unique=True)
    venda_ultimo_mes = Column(Float, default=0.0)
    media_ultimos_6_meses = Column(Float, default=0.0)
    crescimento_percentual = Column(Float, default=0.0)
    top_fabricas_json = Column(Text, nullable=True)
    sugestoes_fabricas_json = Column(Text, nullable=True)
    produtos_recomendados_json = Column(Text, nullable=True)
    produtos_parados_json = Column(Text, nullable=True)
    produtos_risco_inatividade_json = Column(Text, nullable=True)
    produtos_sem_segunda_compra_json = Column(Text, nullable=True)

class FabricaAnalytics(Base):
    __tablename__ = "fabrica_analytics"
    id = Column(Integer, primary_key=True, index=True)
    fabrica_id = Column(Integer, ForeignKey("fabricas.id"))
    regiao_imediata = Column(String(100), index=True)
    total_vendas = Column(Float, default=0.0)
    volume_vendido = Column(Float, default=0.0)
    tendencia_venda = Column(String(50), nullable=True)
    top_produtos_json = Column(Text, nullable=True)

class AlertaComercial(Base):
    __tablename__ = "alerta_comercial"
    id = Column(Integer, primary_key=True, index=True)
    tipo_alerta = Column(String(50), nullable=False)
    cliente_id = Column(Integer, ForeignKey("clientes.id"), nullable=True)
    vendedor_id = Column(Integer, ForeignKey("vendedores.id"), nullable=True)
    fabrica_id = Column(Integer, ForeignKey("fabricas.id"), nullable=True)
    descricao_acao = Column(String(255), nullable=True)
    data_referencia = Column(Date, nullable=True)