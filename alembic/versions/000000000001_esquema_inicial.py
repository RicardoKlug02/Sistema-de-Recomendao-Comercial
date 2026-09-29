"""Esquema comercial original para reconstrução de um banco vazio."""
from alembic import op
import sqlalchemy as sa

revision = "000000000001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("clientes",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("razao_social", sa.String(150), nullable=False),
        sa.Column("nome_fantasia", sa.String(150)),
        sa.Column("cnpj_cpf", sa.String(18)),
        sa.Column("cep", sa.String(10)), sa.Column("grupo_economico", sa.String(100)),
        sa.Column("micro_regiao", sa.String(50)), sa.Column("cidade", sa.String(100)),
        sa.Column("estado", sa.String(2)),
        sa.UniqueConstraint("cnpj_cpf", name="clientes_cnpj_cpf_key"))
    op.create_table("fabricas",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("nome_fantasia", sa.String(100), nullable=False),
        sa.Column("cnpj", sa.String(18)),
        sa.UniqueConstraint("cnpj", name="fabricas_cnpj_key"))
    op.create_table("vendedores",
        sa.Column("id", sa.Integer, primary_key=True), sa.Column("nome", sa.String(100), nullable=False))
    op.create_table("produtos",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("fabrica_id", sa.Integer, sa.ForeignKey("fabricas.id", name="produtos_fabrica_id_fkey")),
        sa.Column("nome", sa.String(150), nullable=False), sa.Column("sku", sa.String(50)),
        sa.UniqueConstraint("sku", name="produtos_sku_key"))
    op.create_table("vendas",
        sa.Column("id", sa.Integer, primary_key=True), sa.Column("numero_pedido", sa.String(50)),
        sa.Column("cliente_id", sa.Integer, sa.ForeignKey("clientes.id", name="vendas_cliente_id_fkey")),
        sa.Column("vendedor_id", sa.Integer, sa.ForeignKey("vendedores.id")),
        sa.Column("fabrica_id", sa.Integer, sa.ForeignKey("fabricas.id")),
        sa.Column("data_venda", sa.Date, nullable=False), sa.Column("valor_total", sa.Float),
        sa.UniqueConstraint("numero_pedido", name="vendas_numero_pedido_key"),
        sa.Index("ix_vendas_numero_pedido", "numero_pedido"))
    op.create_table("itens_venda",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("venda_id", sa.Integer, sa.ForeignKey("vendas.id", name="itens_venda_venda_id_fkey")),
        sa.Column("produto_id", sa.Integer, sa.ForeignKey("produtos.id")),
        sa.Column("quantidade", sa.Integer, nullable=False), sa.Column("preco_unitario", sa.Float, nullable=False))


def downgrade():
    for tabela in ("itens_venda", "vendas", "produtos", "vendedores", "fabricas", "clientes"):
        op.drop_table(tabela)
