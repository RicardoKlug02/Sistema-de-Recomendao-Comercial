"""Classificação explícita e auditável dos pedidos importados."""
from alembic import op
import sqlalchemy as sa

revision = '20261109_revisao_pedidos'
down_revision = '20261028_sincronizacao'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('vendas', sa.Column('classificacao', sa.String(30), nullable=False, server_default='NAO_REVISADO'))
    op.add_column('vendas', sa.Column('considerar_analises', sa.Boolean(), nullable=False, server_default=sa.true()))
    op.add_column('vendas', sa.Column('nova_compra', sa.Boolean(), nullable=False, server_default=sa.true()))
    op.create_table('revisoes_pedido',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('venda_id', sa.Integer(), sa.ForeignKey('vendas.id', ondelete='SET NULL'), nullable=True),
        sa.Column('usuario_id', sa.Integer(), sa.ForeignKey('usuarios.id'), nullable=True),
        sa.Column('classificacao_anterior', sa.String(30), nullable=False),
        sa.Column('classificacao', sa.String(30), nullable=False),
        sa.Column('motivo', sa.Text(), nullable=False),
        sa.Column('evidencia', sa.Text(), nullable=False),
        sa.Column('pedido_original', sa.Text(), nullable=False),
        sa.Column('criado_em', sa.DateTime(timezone=True), nullable=False))
    op.create_index('ix_revisoes_pedido_venda_id', 'revisoes_pedido', ['venda_id'])


def downgrade():
    op.drop_table('revisoes_pedido')
    op.drop_column('vendas', 'considerar_analises')
    op.drop_column('vendas', 'nova_compra')
    op.drop_column('vendas', 'classificacao')
