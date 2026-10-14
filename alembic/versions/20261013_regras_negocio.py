"""Regras comerciais sem modificar pedidos ou produtos históricos."""
from alembic import op
import sqlalchemy as sa

revision = '20261013_regras'
down_revision = '20260929_operacao'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('regras_negocio',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('tipo', sa.String(20), nullable=False),
        sa.Column('fabrica_id', sa.Integer, sa.ForeignKey('fabricas.id'), nullable=False),
        sa.Column('cliente_id', sa.Integer, sa.ForeignKey('clientes.id')),
        sa.Column('uf', sa.String(2)),
        sa.Column('produto_origem_id', sa.Integer, sa.ForeignKey('produtos.id')),
        sa.Column('produto_destino_id', sa.Integer, sa.ForeignKey('produtos.id')),
        sa.Column('excecoes_clientes', sa.JSON, nullable=False, server_default='[]'),
        sa.Column('excecoes_vendedores', sa.JSON, nullable=False, server_default='[]'),
        sa.Column('inicio', sa.Date, nullable=False), sa.Column('fim', sa.Date),
        sa.Column('ativa', sa.Boolean, nullable=False), sa.Column('motivo', sa.Text, nullable=False),
        sa.Column('criado_por', sa.Integer, sa.ForeignKey('usuarios.id')),
        sa.Column('atualizado_por', sa.Integer, sa.ForeignKey('usuarios.id')),
        sa.Column('criado_em', sa.DateTime(timezone=True), nullable=False),
        sa.Column('atualizado_em', sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("tipo IN ('SUBSTITUICAO', 'RESTRICAO')", name='ck_regra_tipo'),
        sa.CheckConstraint('fim IS NULL OR fim >= inicio', name='ck_regra_vigencia'),
        sa.CheckConstraint("(tipo = 'SUBSTITUICAO' AND produto_origem_id IS NOT NULL AND produto_destino_id IS NOT NULL AND produto_origem_id <> produto_destino_id AND uf IS NULL) OR (tipo = 'RESTRICAO' AND produto_origem_id IS NULL AND produto_destino_id IS NULL)", name='ck_regra_produtos'))
    op.create_index('ix_regras_negocio_fabrica_id', 'regras_negocio', ['fabrica_id'])


def downgrade():
    op.drop_table('regras_negocio')
