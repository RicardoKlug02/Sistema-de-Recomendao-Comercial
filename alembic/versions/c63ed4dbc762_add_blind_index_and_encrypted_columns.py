"""add_blind_index_and_encrypted_columns

Revision ID: c63ed4dbc762
Revises: 0ebe3a11b72b
Create Date: 2026-09-14 21:30:01.699295

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c63ed4dbc762'
down_revision: Union[str, Sequence[str], None] = '0ebe3a11b72b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('clientes', sa.Column('cnpj_hash', sa.String(length=64), nullable=True))
    op.alter_column('clientes', 'razao_social',
               existing_type=sa.VARCHAR(length=255),
               type_=sa.String(length=512),
               existing_nullable=False)
    op.alter_column('clientes', 'nome_fantasia',
               existing_type=sa.VARCHAR(length=255),
               type_=sa.String(length=512),
               existing_nullable=True)
    op.alter_column('clientes', 'cnpj_cpf',
               existing_type=sa.VARCHAR(length=64),
               type_=sa.String(length=512),
               existing_nullable=True)
    op.drop_constraint(op.f('clientes_cnpj_cpf_key'), 'clientes', type_='unique')
    op.create_index(op.f('ix_clientes_cnpj_hash'), 'clientes', ['cnpj_hash'], unique=True)
    op.create_index(op.f('ix_clientes_grupo_economico'), 'clientes', ['grupo_economico'], unique=False)
    op.create_index(op.f('ix_clientes_micro_regiao'), 'clientes', ['micro_regiao'], unique=False)
    op.drop_constraint(op.f('fabricas_cnpj_key'), 'fabricas', type_='unique')
    op.create_index(op.f('ix_fabricas_cnpj'), 'fabricas', ['cnpj'], unique=True)
    op.create_index(op.f('ix_fabricas_nome_fantasia'), 'fabricas', ['nome_fantasia'], unique=False)
    op.alter_column('itens_venda', 'venda_id',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('itens_venda', 'produto_id',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.create_index(op.f('ix_itens_venda_produto_id'), 'itens_venda', ['produto_id'], unique=False)
    op.create_index(op.f('ix_itens_venda_venda_id'), 'itens_venda', ['venda_id'], unique=False)
    op.drop_constraint(op.f('itens_venda_venda_id_fkey'), 'itens_venda', type_='foreignkey')
    op.create_foreign_key(None, 'itens_venda', 'vendas', ['venda_id'], ['id'], ondelete='CASCADE')
    op.alter_column('produtos', 'fabrica_id',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.drop_constraint(op.f('produtos_sku_key'), 'produtos', type_='unique')
    op.create_index(op.f('ix_produtos_fabrica_id'), 'produtos', ['fabrica_id'], unique=False)
    op.create_index(op.f('ix_produtos_nome'), 'produtos', ['nome'], unique=False)
    op.create_index(op.f('ix_produtos_sku'), 'produtos', ['sku'], unique=True)
    op.drop_constraint(op.f('produtos_fabrica_id_fkey'), 'produtos', type_='foreignkey')
    op.create_foreign_key(None, 'produtos', 'fabricas', ['fabrica_id'], ['id'], ondelete='RESTRICT')
    op.add_column('usuarios', sa.Column('perfil', sa.String(length=50), nullable=False, server_default='vendedor'))
    op.add_column('usuarios', sa.Column('aprovado', sa.Boolean(), nullable=False, server_default=sa.text('false')))
    op.alter_column('vendas', 'cliente_id',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('vendas', 'fabrica_id',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('vendas', 'valor_total',
               existing_type=sa.DOUBLE_PRECISION(precision=53),
               nullable=False)
    op.create_index(op.f('ix_vendas_cliente_id'), 'vendas', ['cliente_id'], unique=False)
    op.create_index(op.f('ix_vendas_data_venda'), 'vendas', ['data_venda'], unique=False)
    op.create_index(op.f('ix_vendas_fabrica_id'), 'vendas', ['fabrica_id'], unique=False)
    op.create_index(op.f('ix_vendas_vendedor_id'), 'vendas', ['vendedor_id'], unique=False)
    op.drop_constraint(op.f('vendas_cliente_id_fkey'), 'vendas', type_='foreignkey')
    op.create_foreign_key(None, 'vendas', 'clientes', ['cliente_id'], ['id'], ondelete='CASCADE')
    op.create_index(op.f('ix_vendedores_nome'), 'vendedores', ['nome'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_vendedores_nome'), table_name='vendedores')
    op.drop_constraint(None, 'vendas', type_='foreignkey')
    op.create_foreign_key(op.f('vendas_cliente_id_fkey'), 'vendas', 'clientes', ['cliente_id'], ['id'])
    op.drop_index(op.f('ix_vendas_vendedor_id'), table_name='vendas')
    op.drop_index(op.f('ix_vendas_fabrica_id'), table_name='vendas')
    op.drop_index(op.f('ix_vendas_data_venda'), table_name='vendas')
    op.drop_index(op.f('ix_vendas_cliente_id'), table_name='vendas')
    op.alter_column('vendas', 'valor_total',
               existing_type=sa.DOUBLE_PRECISION(precision=53),
               nullable=True)
    op.alter_column('vendas', 'fabrica_id',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('vendas', 'cliente_id',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.drop_column('usuarios', 'aprovado')
    op.drop_column('usuarios', 'perfil')
    op.drop_constraint(None, 'produtos', type_='foreignkey')
    op.create_foreign_key(op.f('produtos_fabrica_id_fkey'), 'produtos', 'fabricas', ['fabrica_id'], ['id'])
    op.drop_index(op.f('ix_produtos_sku'), table_name='produtos')
    op.drop_index(op.f('ix_produtos_nome'), table_name='produtos')
    op.drop_index(op.f('ix_produtos_fabrica_id'), table_name='produtos')
    op.create_unique_constraint(op.f('produtos_sku_key'), 'produtos', ['sku'], postgresql_nulls_not_distinct=False)
    op.alter_column('produtos', 'fabrica_id',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.drop_constraint(None, 'itens_venda', type_='foreignkey')
    op.create_foreign_key(op.f('itens_venda_venda_id_fkey'), 'itens_venda', 'vendas', ['venda_id'], ['id'])
    op.drop_index(op.f('ix_itens_venda_venda_id'), table_name='itens_venda')
    op.drop_index(op.f('ix_itens_venda_produto_id'), table_name='itens_venda')
    op.alter_column('itens_venda', 'produto_id',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('itens_venda', 'venda_id',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.drop_index(op.f('ix_fabricas_nome_fantasia'), table_name='fabricas')
    op.drop_index(op.f('ix_fabricas_cnpj'), table_name='fabricas')
    op.create_unique_constraint(op.f('fabricas_cnpj_key'), 'fabricas', ['cnpj'], postgresql_nulls_not_distinct=False)
    op.drop_index(op.f('ix_clientes_micro_regiao'), table_name='clientes')
    op.drop_index(op.f('ix_clientes_grupo_economico'), table_name='clientes')
    op.drop_index(op.f('ix_clientes_cnpj_hash'), table_name='clientes')
    op.create_unique_constraint(op.f('clientes_cnpj_cpf_key'), 'clientes', ['cnpj_cpf'], postgresql_nulls_not_distinct=False)
    op.alter_column('clientes', 'cnpj_cpf',
               existing_type=sa.String(length=512),
               type_=sa.VARCHAR(length=64),
               existing_nullable=True)
    op.alter_column('clientes', 'nome_fantasia',
               existing_type=sa.String(length=512),
               type_=sa.VARCHAR(length=255),
               existing_nullable=True)
    op.alter_column('clientes', 'razao_social',
               existing_type=sa.String(length=512),
               type_=sa.VARCHAR(length=255),
               existing_nullable=False)
    op.drop_column('clientes', 'cnpj_hash')