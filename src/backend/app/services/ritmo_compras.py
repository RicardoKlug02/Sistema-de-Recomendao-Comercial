"""Variações descritivas entre períodos iguais, sem alertas automáticos de queda."""
from collections import defaultdict
from datetime import timedelta


def limites(ref):
    fim = ref + timedelta(days=1)
    inicio = fim - timedelta(days=30)
    habitual_inicio = inicio - timedelta(days=90)
    return habitual_inicio, inicio, fim


def comparacao(atual, habitual, suficiente):
    variacao = round((atual / habitual - 1) * 100, 1) if suficiente and habitual > 0 else None
    status = "COMPARAVEL" if variacao is not None else (
        "SEM_BASE_COMPARACAO" if suficiente else "HISTORICO_INSUFICIENTE")
    return {"recente": round(float(atual), 2), "media_habitual": round(float(habitual), 2),
            "variacao_pct": variacao, "status": status}


def calcular_ritmo(vendas, ref):
    vendas = [v for v in vendas if v.data_venda <= ref]
    anterior, inicio, fim = limites(ref)
    recente = [v for v in vendas if inicio <= v.data_venda < fim]
    habitual = [v for v in vendas if anterior <= v.data_venda < inicio]
    suficiente = bool(vendas and min(v.data_venda for v in vendas) <= anterior and len(habitual) >= 2)
    return {
        "inicio_recente": inicio.isoformat(), "fim_recente": ref.isoformat(),
        "inicio_habitual": anterior.isoformat(), "fim_habitual": (inicio - timedelta(days=1)).isoformat(),
        "historico_suficiente": suficiente,
        "valor": comparacao(sum(v.valor_total for v in recente), sum(v.valor_total for v in habitual) / 3, suficiente),
        "pedidos": comparacao(len(recente), len(habitual) / 3, suficiente),
    }


def comparar_produtos(registros, ref, suficiente):
    anterior, inicio, fim = limites(ref)
    produtos, fabricas_incompletas = {}, set()
    for r in registros:
        if not anterior <= r.data_venda < fim:
            continue
        if r.produto_id is None:
            fabricas_incompletas.add(r.fabrica_id)
            continue
        p = produtos.setdefault(r.produto_id, {"nome": r.produto_nome, "sku": r.sku, "fabrica_id": r.fabrica_id,
                                             "compras": defaultdict(float)})
        p["compras"][r.data_venda] += r.quantidade
    resultado = []
    for pid, p in produtos.items():
        recente = sum(q for d, q in p["compras"].items() if inicio <= d < fim)
        habitual = sum(q for d, q in p["compras"].items() if anterior <= d < inicio) / 3
        datas_anteriores = sum(anterior <= d < inicio for d in p["compras"])
        incompleto = p["fabrica_id"] in fabricas_incompletas
        c = comparacao(recente, habitual, suficiente and datas_anteriores >= 2 and not incompleto)
        if incompleto:
            c["status"] = "ITENS_INCOMPLETOS"
        resultado.append({"produto_id": pid, "nome": p["nome"], "sku": p["sku"], **c})
    return sorted(resultado, key=lambda p: (p["variacao_pct"] is None, p["variacao_pct"] or 0, p["nome"]))
