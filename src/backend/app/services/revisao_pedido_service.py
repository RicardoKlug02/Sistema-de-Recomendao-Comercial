import json
from src.backend.app.models import RevisaoPedido


def registrar_revisao(db, venda, classificacao, motivo, evidencia='', usuario_id=None):
    evento = RevisaoPedido(venda_id=venda.id, usuario_id=usuario_id,
        classificacao_anterior=venda.classificacao, classificacao=classificacao,
        motivo=motivo, evidencia=evidencia,
        pedido_original=json.dumps({'venda_id': venda.id, 'pedido': venda.numero_pedido,
            'cliente_id': venda.cliente_id, 'fabrica_id': venda.fabrica_id,
            'data': venda.data_venda.isoformat(), 'valor_total': venda.valor_total}))
    venda.classificacao = classificacao
    venda.considerar_analises = classificacao not in ('BONIFICACAO', 'DUPLICIDADE', 'OUTRO_TIPO')
    venda.nova_compra = classificacao != 'AJUSTE_COMISSIONADO'
    db.add(evento)
    return evento
