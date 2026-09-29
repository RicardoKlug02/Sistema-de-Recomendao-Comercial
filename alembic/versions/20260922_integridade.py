"""Valores decimais, categoria, sessões revogáveis e histórico de cargas."""

from alembic import op
import sqlalchemy as sa

revision = "20260922_integridade"
down_revision = "c63ed4dbc762"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "usuarios",
        sa.Column("versao_sessao", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column("produtos", sa.Column("categoria", sa.String(100)))
    op.create_index("ix_produtos_categoria", "produtos", ["categoria"])
    op.alter_column(
        "vendas",
        "valor_total",
        existing_type=sa.Float(),
        type_=sa.Numeric(16, 2),
        postgresql_using="round(valor_total::numeric, 2)",
    )
    op.alter_column(
        "itens_venda",
        "preco_unitario",
        existing_type=sa.Float(),
        type_=sa.Numeric(16, 2),
        postgresql_using="round(preco_unitario::numeric, 2)",
    )
    op.add_column(
        "itens_venda", sa.Column("subtotal", sa.Numeric(16, 2), nullable=True)
    )
    op.execute(
        "UPDATE itens_venda SET subtotal = round((quantidade * preco_unitario)::numeric, 2)"
    )
    op.alter_column("itens_venda", "subtotal", nullable=False)
    op.create_table(
        "importacoes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("arquivos", sa.String(512), nullable=False),
        sa.Column("usuario", sa.String(150), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("mensagem", sa.Text(), nullable=False),
        sa.Column("criado_em", sa.DateTime(), nullable=False),
    )


def downgrade():
    op.drop_table("importacoes")
    op.drop_column("itens_venda", "subtotal")
    op.alter_column(
        "itens_venda",
        "preco_unitario",
        type_=sa.Float(),
        existing_type=sa.Numeric(16, 2),
    )
    op.alter_column(
        "vendas", "valor_total", type_=sa.Float(), existing_type=sa.Numeric(16, 2)
    )
    op.drop_index("ix_produtos_categoria", "produtos")
    op.drop_column("produtos", "categoria")
    op.drop_column("usuarios", "versao_sessao")
