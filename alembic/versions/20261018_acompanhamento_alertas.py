"""Histórico de acompanhamento dos alertas por cliente comercial."""
from alembic import op
import sqlalchemy as sa

revision = '20261018_acoes'
down_revision = '20261018_historico'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('acoes_alerta',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('cliente_id', sa.Integer, sa.ForeignKey('clientes.id'), nullable=False),
        sa.Column('usuario_id', sa.Integer, sa.ForeignKey('usuarios.id'), nullable=False),
        sa.Column('assinatura', sa.String(64), nullable=False),
        sa.Column('situacao', sa.String(30), nullable=False),
        sa.Column('motivo', sa.Text, nullable=False),
        sa.Column('proximo_contato', sa.Date),
        sa.Column('criado_em', sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("situacao IN ('PENDENTE','CONTATADO','AGUARDANDO_RETORNO','DISPENSADO')", name='ck_acao_alerta_situacao'))
    op.create_index('ix_acoes_alerta_cliente_id','acoes_alerta',['cliente_id'])


def downgrade():
    op.drop_table('acoes_alerta')
