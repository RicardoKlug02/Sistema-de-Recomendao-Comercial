from datetime import date
from sqlalchemy import func
from src.backend.app.models import Venda, ItemVenda


def conferir_base(db, resumo):
    """Posição persistida após a carga, no intervalo dos cabeçalhos válidos."""
    inicio, fim = resumo.get('inicio'), resumo.get('fim')
    if not inicio or not fim:
        # A sincronização de mês vazio ainda possui um escopo verificável.
        if resumo.get('modo') != 'sincronizar_mes' or not resumo.get('mes'):
            return None
        import calendar
        ano, mes = map(int, resumo['mes'].split('-'))
        inicio, fim = date(ano, mes, 1), date(ano, mes, calendar.monthrange(ano, mes)[1])
    inicio = date.fromisoformat(inicio) if isinstance(inicio, str) else inicio
    fim = date.fromisoformat(fim) if isinstance(fim, str) else fim
    if resumo.get('modo') == 'sincronizar_mes':
        import calendar
        ano, mes = map(int, resumo['mes'].split('-'))
        inicio, fim = date(ano, mes, 1), date(ano, mes, calendar.monthrange(ano, mes)[1])
    db.flush()
    q = db.query(Venda).execution_options(incluir_vendas_excluidas=True).filter(
        Venda.data_venda >= inicio, Venda.data_venda <= fim)
    comerciais = q.filter(Venda.considerar_analises.is_(True))
    compras = comerciais.filter(Venda.nova_compra.is_(True))
    quantidade, valor = comerciais.with_entities(func.count(Venda.id), func.coalesce(func.sum(Venda.valor_total), 0)).one()
    return {'inicio': inicio.isoformat(), 'fim': fim.isoformat(), 'registros_comissionados': quantidade,
            'valor_comissionado': round(float(valor), 2), 'pedidos_compra': compras.count(),
            'ajustes_comissionados': comerciais.filter(Venda.nova_compra.is_(False)).count(),
            'fora_analises': q.filter(Venda.considerar_analises.is_(False)).count(),
            'pedidos_sem_itens': compras.filter(~Venda.itens.any()).count(),
            'pendentes_sem_itens': compras.filter(~Venda.itens.any(), Venda.classificacao == 'NAO_REVISADO').count(),
            'linhas_itens': db.query(func.count(ItemVenda.id)).filter(
                ItemVenda.venda_id.in_(compras.with_entities(Venda.id))).scalar()}
