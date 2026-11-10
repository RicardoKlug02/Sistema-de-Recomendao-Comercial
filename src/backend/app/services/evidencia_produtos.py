"""Pedidos sem itens não confirmam nem descartam a recompra de um código."""


def origem_pedido(registro):
    """Evidência fiscal, sem confundir ausência na base com venda direta."""
    return {
        "venda_id": getattr(registro, "venda_id", None),
        "pedido": getattr(registro, "numero_pedido", None),
        "data": registro.data_venda.isoformat(),
        "cliente_id": getattr(registro, "cliente_id", None),
        "cliente": getattr(registro, "cliente_nome", None),
        "cnpj_cpf": getattr(registro, "cnpj_cpf", None),
        "fabrica": getattr(registro, "fabrica_nome", None),
    }


def origens_produtos(registros):
    por_produto = {}
    for r in registros:
        if r.produto_id is None:
            continue
        pedidos = por_produto.setdefault(r.produto_id, {})
        chave = getattr(r, "venda_id", r.data_venda)
        pedido = pedidos.setdefault(chave, {**origem_pedido(r), "quantidade": 0, "valor_itens": 0,
                                             "precos_disponiveis": True, "codigos": []})
        pedido["quantidade"] += float(r.quantidade or 0)
        pedido["valor_itens"] += float(r.quantidade or 0) * float(getattr(r, 'preco_unitario', 0) or 0)
        if getattr(r, 'preco_unitario', None) is None:
            pedido['precos_disponiveis'] = False
        codigo = getattr(r, "sku_original", r.sku)
        if codigo not in pedido["codigos"]:
            pedido["codigos"].append(codigo)
    return {pid: {"fonte": "Itens dos pedidos importados", "pedidos": list(pedidos.values())}
            for pid, pedidos in por_produto.items()}


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
