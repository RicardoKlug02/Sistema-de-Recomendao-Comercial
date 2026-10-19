"""Pedidos sem itens não confirmam nem descartam a recompra de um código."""


def ultimos_pedidos_sem_itens(registros):
    ultimos = {}
    for r in registros:
        if r.produto_id is None:
            ultimos[r.fabrica_id] = max(ultimos.get(r.fabrica_id, r.data_venda), r.data_venda)
    return ultimos


def recompra_nao_confirmada(ultima_compra, pedido_sem_itens):
    return pedido_sem_itens is not None and pedido_sem_itens > ultima_compra


def ultimos_pedidos_desconhecidos(db, ref, identidade):
    from src.backend.app.models import Venda
    resultado = {}
    for v in db.query(Venda.cliente_id,Venda.fabrica_id,Venda.data_venda).filter(
            Venda.data_venda <= ref, ~Venda.itens.any()).order_by(Venda.data_venda):
        resultado[(identidade.id(v.cliente_id),v.fabrica_id)] = v.data_venda
    return resultado
