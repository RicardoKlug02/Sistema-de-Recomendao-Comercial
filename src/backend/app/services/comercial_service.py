"""Indicadores e alertas calculados a partir das vendas, incluindo pedidos sem itens."""
from collections import defaultdict
from datetime import date
from dateutil.relativedelta import relativedelta
from sqlalchemy import func
from src.backend.app.models import Cliente, Fabrica, Venda, Vendedor, Produto, ItemVenda


class ComercialService:
    def __init__(self, db):
        self.db = db

    def painel(self, mes=None, vendedor_id=None):
        ref = date.today()
        todas = self.db.query(Venda).filter(Venda.data_venda <= ref).order_by(Venda.data_venda, Venda.id).all()
        mes = mes or (todas[-1].data_venda.strftime("%Y-%m") if todas else ref.strftime("%Y-%m"))
        inicio = date.fromisoformat(mes + "-01")
        fim = inicio + relativedelta(months=1)
        vendas = [v for v in todas if inicio <= v.data_venda < fim and
                  (vendedor_id is None or v.vendedor_id == vendedor_id)]
        anteriores = [v for v in todas if inicio - relativedelta(months=1) <= v.data_venda < inicio and
                      (vendedor_id is None or v.vendedor_id == vendedor_id)]
        clientes = {c.id: c for c in self.db.query(Cliente).all()}
        fabricas = {f.id: f for f in self.db.query(Fabrica).all()}
        primeira, primeira_fabrica, ultima, reativados = {}, {}, {}, set()
        ids_vendas = {v.id for v in vendas}
        for venda in todas:
            primeira.setdefault(venda.cliente_id, venda)
            primeira_fabrica.setdefault((venda.cliente_id, venda.fabrica_id), venda)
            if venda.id in ids_vendas and venda.cliente_id in ultima and (venda.data_venda - ultima[venda.cliente_id]).days >= 90:
                reativados.add(venda.cliente_id)
            ultima[venda.cliente_id] = venda.data_venda
        atendidos = {v.cliente_id for v in vendas}
        aberturas = [v for v in primeira_fabrica.values() if v.id in ids_vendas]
        novos = sum(v.id in ids_vendas for v in primeira.values())
        ids_com_itens = {r[0] for r in self.db.query(ItemVenda.venda_id).filter(ItemVenda.venda_id.in_([v.id for v in vendas])).distinct()}
        total = sum(v.valor_total for v in vendas)
        mensal, fat_clientes, fat_fabricas, fat_anteriores = defaultdict(float), defaultdict(float), defaultdict(float), defaultdict(float)
        for v in todas:
            if vendedor_id is None or v.vendedor_id == vendedor_id:
                mensal[v.data_venda.strftime("%Y-%m")] += v.valor_total
        for v in vendas:
            fat_clientes[v.cliente_id] += v.valor_total
            fat_fabricas[v.fabrica_id] += v.valor_total
        for v in anteriores:
            fat_anteriores[v.fabrica_id] += v.valor_total
        regioes = defaultdict(float)
        for v in vendas:
            c = clientes[v.cliente_id]
            regioes[(c.micro_regiao or "Região não identificada", c.estado or "UF não informada")] += v.valor_total
        produtos = []
        if vendas:
            linhas = (self.db.query(Produto.id, Produto.nome, Produto.sku, func.sum(ItemVenda.quantidade).label("qtd"),
                                   func.sum(ItemVenda.quantidade * ItemVenda.preco_unitario).label("valor"))
                      .join(ItemVenda, ItemVenda.produto_id == Produto.id)
                      .filter(ItemVenda.venda_id.in_([v.id for v in vendas]))
                      .group_by(Produto.id, Produto.nome, Produto.sku)
                      .order_by(func.sum(ItemVenda.quantidade * ItemVenda.preco_unitario).desc()).limit(10).all())
            produtos = [{"id": r.id, "nome": r.nome, "sku": r.sku, "quantidade": int(r.qtd),
                         "valor": round(float(r.valor), 2)} for r in linhas]
        meses = [(inicio - relativedelta(months=i)).strftime("%Y-%m") for i in range(11, -1, -1)]
        return {"mes": mes, "indicadores": {
            "venda_total": round(total, 2), "pedidos_emitidos": len(vendas),
            "clientes_atendidos": len(atendidos), "ticket_medio": round(total / len(vendas), 2) if vendas else 0,
            "clientes_novos": novos, "aberturas_cliente_fabrica": len(aberturas),
            "clientes_reativados": len(reativados),
            "pedidos_sem_itens": sum(v.id not in ids_com_itens for v in vendas)},
            "faturamento_mensal": [{"mes": m, "valor": round(mensal[m], 2)} for m in meses],
            "clientes": [{"id": c, "nome": clientes[c].razao_social, "valor": round(valor, 2)}
                         for c, valor in sorted(fat_clientes.items(), key=lambda p: p[1], reverse=True)[:5]],
            "fabricas": [{"id": f, "nome": fabricas[f].nome_fantasia, "valor": round(valor, 2),
                          "variacao_pct": round((valor / fat_anteriores[f] - 1) * 100, 1) if fat_anteriores[f] else None}
                         for f, valor in sorted(fat_fabricas.items(), key=lambda p: p[1], reverse=True)[:10]],
            "produtos": produtos,
            "regioes": [{"nome": r, "uf": uf, "valor": round(valor, 2)} for (r, uf), valor in sorted(regioes.items(), key=lambda p: p[1], reverse=True)],
            "aberturas": [{"cliente_id": v.cliente_id, "cliente": clientes[v.cliente_id].razao_social,
                           "fabrica": fabricas[v.fabrica_id].nome_fantasia, "data": v.data_venda.isoformat(),
                           "novo_no_escritorio": primeira[v.cliente_id].id == v.id} for v in aberturas],
            "fabricas_quentes": [{"nome": fabricas[f].nome_fantasia, "crescimento": round((valor / fat_anteriores[f] - 1) * 100, 1)}
                                for f, valor in fat_fabricas.items() if fat_anteriores[f] and valor > fat_anteriores[f]]}

    def alertas(self, vendedor_id=None):
        ref = date.today()
        vendas = self.db.query(Venda).filter(Venda.data_venda <= ref).order_by(Venda.data_venda, Venda.id).all()
        clientes = {c.id: c for c in self.db.query(Cliente).all()}
        fabricas = {f.id: f for f in self.db.query(Fabrica).all()}
        por_cliente, por_fabrica, por_produto = defaultdict(list), defaultdict(list), defaultdict(dict)
        for v in vendas:
            por_cliente[v.cliente_id].append(v)
            por_fabrica[(v.cliente_id, v.fabrica_id)].append(v)
        itens = (self.db.query(Venda.cliente_id, Venda.data_venda, Venda.vendedor_id, ItemVenda.produto_id, Produto.nome)
                 .select_from(Venda).join(ItemVenda, ItemVenda.venda_id == Venda.id)
                 .join(Produto, Produto.id == ItemVenda.produto_id).filter(Venda.data_venda <= ref).all())
        for r in itens:
            por_produto[(r.cliente_id, r.produto_id)][r.data_venda] = r
        resultado = []
        def adicionar(tipo, cliente_id, descricao, dias, prioridade, venda, fabrica_id=None, produto_id=None):
            if vendedor_id is not None and venda.vendedor_id != vendedor_id:
                return
            resultado.append({"id": f"{tipo}:{cliente_id}:{fabrica_id or produto_id or 0}", "tipo": tipo,
                              "cliente_id": cliente_id, "cliente": clientes[cliente_id].razao_social,
                              "descricao": descricao, "dias": dias, "prioridade": prioridade,
                              "fabrica_id": fabrica_id, "produto_id": produto_id})
        for cid, historico in por_cliente.items():
            ultima = historico[-1]
            dias = (ref - ultima.data_venda).days
            if len(historico) == 1 and dias >= 14:
                adicionar("SEGUNDO_PEDIDO", cid, "Contatar cliente para o segundo pedido.", dias, 2, ultima)
            if dias >= 90:
                adicionar("CLIENTE_INATIVO", cid, "Cliente sem pedidos há pelo menos 90 dias.", dias, 1, ultima)
        for (cid, fid), historico in por_fabrica.items():
            ultima = historico[-1]
            dias = (ref - ultima.data_venda).days
            if dias >= 76:
                adicionar("FABRICA_INATIVA" if dias >= 90 else "FABRICA_EM_RISCO", cid,
                          f"{fabricas[fid].nome_fantasia}: " + ("inativa." if dias >= 90 else f"inatividade em {90 - dias} dias."),
                          dias, 1 if dias >= 90 else 2, ultima, fabrica_id=fid)
        for (cid, pid), compras in por_produto.items():
            datas = sorted(compras)
            if len(datas) < 2:
                continue
            ciclo = max(1, sum((b - a).days for a, b in zip(datas, datas[1:])) / (len(datas) - 1))
            dias = (ref - datas[-1]).days
            if dias >= max(30, ciclo * 1.5):
                meta = compras[datas[-1]]
                adicionar("PRODUTO_EM_RISCO", cid, f"{meta.nome}: {dias} dias sem comprar (ciclo médio {ciclo:.0f} dias).",
                          dias, 1 if dias >= ciclo * 2.5 else 2, meta, produto_id=pid)
        return sorted(resultado, key=lambda a: (a["prioridade"], -a["dias"], a["cliente_id"]))
