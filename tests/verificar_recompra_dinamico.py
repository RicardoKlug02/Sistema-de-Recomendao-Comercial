import sys
from pathlib import Path

raiz = Path(__file__).resolve().parent.parent
if str(raiz) not in sys.path:
    sys.path.insert(0, str(raiz))

from sqlalchemy import func
from sqlalchemy.orm import Session
from src.backend.app.core.database import engine
from src.backend.app.core.security import decrypt_data
from src.backend.app.models.cliente import Cliente
from src.backend.app.models.item_venda import ItemVenda
from src.backend.app.models.venda import Venda
from src.backend.app.services.recompra_service import RecompraService

with Session(engine) as session:
    # 1. Localiza um cliente que possua compras repetidas do mesmo produto
    subquery = (
        session.query(
            Venda.cliente_id,
            ItemVenda.produto_id,
            func.count(func.distinct(Venda.data_venda)).label("qtd_datas"),
        )
        .join(ItemVenda, ItemVenda.venda_id == Venda.id)
        .group_by(Venda.cliente_id, ItemVenda.produto_id)
        .having(func.count(func.distinct(Venda.data_venda)) >= 2)
        .subquery()
    )

    candidato = (
        session.query(Cliente)
        .join(subquery, subquery.c.cliente_id == Cliente.id)
        .first()
    )

    if not candidato:
        print("Nenhum cliente possui 2 ou mais compras com datas diferentes no banco.")
        print("Dica: Importe mais meses de vendas para gerar intervalos temporais.")
        sys.exit(0)

    # 2. Executa a análise de recompra para o cliente identificado
    service = RecompraService(db_session=session)
    nome_real = decrypt_data(candidato.razao_social)

    print("\n" + "=" * 80)
    print(f"CLIENTE SELECIONADO PARA TESTE: ID {candidato.id} - {nome_real}")
    print(f"Grupo Econômico: {candidato.grupo_economico}")
    print("=" * 80 + "\n")

    alertas = service.analisar_oportunidades_cliente(cliente_id=candidato.id)

    if not alertas:
        print("Nenhuma oportunidade calculada.")
    else:
        for item in alertas:
            print(f"★ [{item['sku']}] {item['nome']}")
            print(f"   Status: {item['status']}")
            print(
                f"   Ciclo Médio: cada {item['periodicidade_media_dias']} dias | "
                f"Total de Compras: {item['total_compras_historico']}"
            )
            print(
                f"   Última Compra: há {item['dias_desde_ultima_compra']} dias | "
                f"Atraso Estimado: {item['dias_atraso']} dias"
            )
            print(f"   Previsão de Compra: {item['previsao_proxima_compra']}")
            print(f"   Volume habitual: {item['volume_medio_pedido']} un.")
            print("-" * 80)