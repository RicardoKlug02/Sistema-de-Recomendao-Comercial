"""Permite escolher se a substituição unifica compras anteriores à vigência."""
from alembic import op
import sqlalchemy as sa

revision = '20261018_historico'
down_revision = '20261013_regras'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('regras_negocio', sa.Column('unificar_historico', sa.Boolean(), nullable=False, server_default=sa.true()))


def downgrade():
    op.drop_column('regras_negocio', 'unificar_historico')
