"""Resultados declarados no acompanhamento comercial."""
from alembic import op

revision = '20261109_resultados_acoes'
down_revision = '20261109_revisao_pedidos'
branch_labels = None
depends_on = None


def upgrade():
    op.drop_constraint('ck_acao_alerta_situacao', 'acoes_alerta', type_='check')
    op.create_check_constraint('ck_acao_alerta_situacao', 'acoes_alerta',
        "situacao IN ('PENDENTE','CONTATADO','AGUARDANDO_RETORNO','DISPENSADO','RECOMPRA_REALIZADA','PRODUTO_DESCONTINUADO')")


def downgrade():
    op.execute("UPDATE acoes_alerta SET motivo = '[Resultado: ' || situacao || '] ' || motivo, "
               "situacao = 'CONTATADO' WHERE situacao IN ('RECOMPRA_REALIZADA','PRODUTO_DESCONTINUADO')")
    op.drop_constraint('ck_acao_alerta_situacao', 'acoes_alerta', type_='check')
    op.create_check_constraint('ck_acao_alerta_situacao', 'acoes_alerta',
        "situacao IN ('PENDENTE','CONTATADO','AGUARDANDO_RETORNO','DISPENSADO')")
