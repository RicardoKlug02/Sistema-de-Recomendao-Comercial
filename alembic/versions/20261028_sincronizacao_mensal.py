"""Registra o escopo e o resultado das sincronizações mensais de pedidos."""
from alembic import op
import sqlalchemy as sa

revision = "20261028_sincronizacao"
down_revision = "20261018_acoes"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("importacoes", sa.Column("resumo_json", sa.Text(), nullable=False, server_default="{}"))


def downgrade():
    op.drop_column("importacoes", "resumo_json")
