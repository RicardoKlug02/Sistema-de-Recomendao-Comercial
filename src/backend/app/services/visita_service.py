from src.backend.app.services.cliente_service import ClienteService
from src.backend.app.services.datas import hoje_comercial


def preparar_visita(db, cliente_id, entrada):
    ficha = ClienteService(db).obter_dossie_cliente(
        cliente_id, agrupar_rede=entrada.agrupar_rede, fabrica_id=entrada.fabrica_id)
    if ficha is None:
        return None
    selecionados = None if entrada.produtos_ids is None else set(entrada.produtos_ids)
    secoes = []
    for chave, titulo, ativo in [('produtos_em_abandono', 'Itens em abandono', entrada.abandono),
                                ('sugestoes_reposicao', 'Sugestões de recompra', entrada.recompra)]:
        itens = []
        if not ativo:
            continue
        for produto in ficha.get(chave, []):
            if selecionados is not None and produto['produto_id'] not in selecionados:
                continue
            pedidos = produto.get('origem', {}).get('pedidos', [])
            ultima = max(pedidos, key=lambda p: (p['data'], p.get('venda_id') or 0), default={})
            quantidade = ultima.get('quantidade', 0)
            motivo = (f"{produto['dias_parado']} dias sem compra; ciclo médio de {produto['ciclo_habitual']} dias; "
                      f"{produto['total_vezes_comprado']} datas de compra."
                      if chave == 'produtos_em_abandono' else
                      f"{produto['status']}; ciclo médio de {produto['ciclo_medio']} dias; "
                      f"{produto['dias_desde_ultima']} dias desde a última compra. "
                      f"Volume habitual: {produto['volume_habitual']:g} unidades (referência histórica).")
            itens.append({**produto, 'ultima': ultima, 'motivo': motivo,
                          'preco': ultima.get('valor_itens', 0) / quantidade
                          if quantidade and ultima.get('precos_disponiveis') else None})
        secoes.append({'titulo': titulo, 'itens': itens})
    return {'cliente': ficha['razao_social'], 'rede': ficha.get('grupo_economico'),
            'cadastros': ficha['cadastros_fiscais'], 'origem': ficha['origem'],
            'referencia': hoje_comercial().isoformat(), 'secoes': secoes,
            'mostrar_precos': entrada.mostrar_precos,
            'sem_confirmacao': len(ficha.get('produtos_sem_confirmacao', [])),
            'fabrica': next((f['fabrica'] for f in ficha.get('resumo_fabricas', [])
                             if f['fabrica_id'] == entrada.fabrica_id),
                            'Todas' if entrada.fabrica_id is None else f'Fábrica {entrada.fabrica_id}')}
