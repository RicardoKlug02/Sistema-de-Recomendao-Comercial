"""Identificadores por fábrica, campos cifrados e histórico de cargas."""
from alembic import op
import sqlalchemy as sa

revision = "20260929_operacao"
down_revision = "c63ed4dbc762"
branch_labels = None
depends_on = None


def upgrade():
    for campo in ("razao_social", "nome_fantasia", "cnpj_cpf"):
        op.alter_column("clientes", campo, type_=sa.Text(), existing_type=sa.String(512))
    op.drop_constraint("vendas_numero_pedido_key", "vendas", type_="unique")
    op.create_unique_constraint("uq_venda_fabrica_pedido", "vendas", ["fabrica_id", "numero_pedido"])
    op.drop_index("ix_produtos_sku", table_name="produtos")
    op.create_index("ix_produtos_sku", "produtos", ["sku"], unique=False)
    op.create_unique_constraint("uq_produto_fabrica_sku", "produtos", ["fabrica_id", "sku"])
    op.create_table("importacoes",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("arquivo", sa.String(255), nullable=False),
        sa.Column("arquivo_itens", sa.String(255), nullable=False),
        sa.Column("usuario", sa.String(150), nullable=False),
        sa.Column("criado_em", sa.DateTime, nullable=False),
        *[sa.Column(n, sa.Integer, nullable=False) for n in
          ("processados", "adicionados", "atualizados", "itens", "pedidos_sem_itens")],
        sa.Column("avisos_json", sa.Text, nullable=False))
    op.create_table("resumo_vendas_geral",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("ano_mes", sa.String(7), index=True),
        sa.Column("regiao_imediata", sa.String(100), index=True),
        sa.Column("vendedor_id", sa.Integer), sa.Column("fabrica_id", sa.Integer),
        sa.Column("total_vendas", sa.Float), sa.Column("quantidade_pedidos", sa.Integer),
        sa.Column("ticket_medio", sa.Float))
    op.create_table("cliente_analytics",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("cliente_id", sa.Integer, sa.ForeignKey("clientes.id"), unique=True),
        *[sa.Column(n, sa.Float) for n in ("venda_ultimo_mes", "media_ultimos_6_meses", "crescimento_percentual")],
        *[sa.Column(n, sa.Text) for n in ("top_fabricas_json", "sugestoes_fabricas_json", "produtos_recomendados_json",
          "produtos_parados_json", "produtos_risco_inatividade_json", "produtos_sem_segunda_compra_json")])
    op.create_table("fabrica_analytics",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("fabrica_id", sa.Integer, sa.ForeignKey("fabricas.id")),
        sa.Column("regiao_imediata", sa.String(100), index=True),
        sa.Column("total_vendas", sa.Float), sa.Column("volume_vendido", sa.Float),
        sa.Column("tendencia_venda", sa.String(50)), sa.Column("top_produtos_json", sa.Text))
    op.create_table("alerta_comercial",
        sa.Column("id", sa.Integer, primary_key=True), sa.Column("tipo_alerta", sa.String(50), nullable=False),
        sa.Column("cliente_id", sa.Integer, sa.ForeignKey("clientes.id")),
        sa.Column("vendedor_id", sa.Integer, sa.ForeignKey("vendedores.id")),
        sa.Column("fabrica_id", sa.Integer, sa.ForeignKey("fabricas.id")),
        sa.Column("descricao_acao", sa.String(255)), sa.Column("data_referencia", sa.Date))


def downgrade():
    raise RuntimeError("Esta revisão não tem downgrade destrutivo automático. Restaure um backup.")
