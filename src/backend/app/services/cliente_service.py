class ClienteService:
    def __init__(self, db_session: Session):
        self.db = db_session

    def buscar_por_termo(self, termo: str, limite: int = 8):
        """Busca rápida por Razão Social (case-insensitive) ou CNPJ"""
        filtro = f"%{termo}%"
        return (
            self.db.query(Cliente.id, Cliente.razao_social, Cliente.cnpj)
            .filter(
                (Cliente.razao_social.ilike(filtro)) | 
                (Cliente.cnpj.like(filtro))
            )
            .limit(limite)
            .all()
        )

from sqlalchemy.orm import Session
from sqlalchemy import func, distinct
from app.models import Cliente, Regiao, Pedido, ItemPedido, Produto # Ajuste conforme seus models

class ClienteService:
    def __init__(self, db_session: Session):
        self.db = db_session

    def obter_relatorio_completo(self, cliente_id: int):
        inicio_mes, fim_mes, inicio_6m = obter_janelas_temporais()

        # 1. Dados Cadastrais e Métricas do Mês Cheio
        dados_base = (
            self.db.query(
                Cliente.id,
                Cliente.razao_social,
                Cliente.cnpj,
                Regiao.nome.label("regiao"),
                func.coalesce(func.sum(Pedido.valor_total), 0.0).label("vendas_mes"),
                func.count(Pedido.id).label("pedidos_mes")
            )
            .join(Regiao, Cliente.regiao_id == Regiao.id)
            .outerjoin(
                Pedido,
                (Pedido.cliente_id == Cliente.id) & 
                (Pedido.data >= inicio_mes) & 
                (Pedido.data <= fim_mes)
            )
            .filter(Cliente.id == cliente_id)
            .group_by(Cliente.id, Regiao.nome)
            .first()
        )

        if not dados_base:
            return None

        # 2. Itens comprados nos últimos 6 meses
        itens_6m = (
            self.db.query(
                Produto.id.label("produto_id"),
                Produto.nome.label("nome_produto"),
                func.sum(ItemPedido.quantidade).label("quantidade"),
                func.sum(ItemPedido.valor_total).label("valor_total"),
                func.max(Pedido.data).label("ultima_compra")
            )
            .join(ItemPedido, ItemPedido.produto_id == Produto.id)
            .join(Pedido, ItemPedido.pedido_id == Pedido.id)
            .filter(
                Pedido.cliente_id == cliente_id,
                Pedido.data >= inicio_6m,
                Pedido.data <= fim_mes
            )
            .group_by(Produto.id, Produto.nome)
            .order_by(func.sum(ItemPedido.valor_total).desc())
            .all()
        )

        # 3. Itens Inativos (Comprou historicamente, mas NÃO comprou nos últimos 6 meses)
        ids_comprados_recentemente = [i.produto_id for i in itens_6m]
        
        itens_inativos_query = (
            self.db.query(
                Produto.id.label("produto_id"),
                Produto.nome.label("nome_produto"),
                func.sum(ItemPedido.quantidade).label("quantidade"),
                func.sum(ItemPedido.valor_total).label("valor_total"),
                func.max(Pedido.data).label("ultima_compra")
            )
            .join(ItemPedido, ItemPedido.produto_id == Produto.id)
            .join(Pedido, ItemPedido.pedido_id == Pedido.id)
            .filter(
                Pedido.cliente_id == cliente_id,
                Pedido.data < inicio_6m
            )
        )
        if ids_comprados_recentemente:
            itens_inativos_query = itens_inativos_query.filter(Produto.id.notin_(ids_comprados_recentemente))
            
        itens_inativos = (
            itens_inativos_query
            .group_by(Produto.id, Produto.nome)
            .order_by(func.max(Pedido.data).desc())
            .limit(10)
            .all()
        )

        # 4. Recomendações (Ex: Produtos mais vendidos na região do cliente que ele ainda não compra)
        produtos_recomendados = (
            self.db.query(
                Produto.id.label("produto_id"),
                Produto.nome.label("nome_produto"),
                func.count(distinct(Pedido.cliente_id)).label("penetracao_regiao")
            )
            .join(ItemPedido, ItemPedido.produto_id == Produto.id)
            .join(Pedido, ItemPedido.pedido_id == Pedido.id)
            .join(Cliente, Pedido.cliente_id == Cliente.id)
            .filter(
                Cliente.regiao_id == Cliente.regiao_id, # Mesma região
                Pedido.data >= inicio_6m
            )
        )
        if ids_comprados_recentemente:
            produtos_recomendados = produtos_recomendados.filter(Produto.id.notin_(ids_comprados_recentemente))

        recomendacoes_raw = (
            produtos_recomendados
            .group_by(Produto.id, Produto.nome)
            .order_by(func.count(distinct(Pedido.cliente_id)).desc())
            .limit(5)
            .all()
        )

        recomendacoes = [
            {
                "produto_id": r.produto_id,
                "nome_produto": r.nome_produto,
                "motivo": "Popular na sua região",
                "score_relevancia": float(r.penetracao_regiao)
            }
            for r in recomendacoes_raw
        ]

        ticket_medio = (dados_base.vendas_mes / dados_base.pedidos_mes) if dados_base.pedidos_mes > 0 else 0.0

        return {
            "id": dados_base.id,
            "razao_social": dados_base.razao_social,
            "cnpj": dados_base.cnpj,
            "regiao": dados_base.regiao,
            "mes_referencia": inicio_mes.strftime("%m/%Y"),
            "vendas_mes_fechado": float(dados_base.vendas_mes),
            "pedidos_mes_fechado": int(dados_base.pedidos_mes),
            "ticket_medio": round(ticket_medio, 2),
            "itens_inclusos_ultimos_6m": [
                {
                    "produto_id": i.produto_id,
                    "nome_produto": i.nome_produto,
                    "quantidade": int(i.quantidade),
                    "valor_total": float(i.valor_total),
                    "ultima_compra": i.ultima_compra.strftime("%d/%m/%Y") if i.ultima_compra else None
                } for i in itens_6m
            ],
            "itens_inativos": [
                {
                    "produto_id": i.produto_id,
                    "nome_produto": i.nome_produto,
                    "quantidade": int(i.quantidade),
                    "valor_total": float(i.valor_total),
                    "ultima_compra": i.ultima_compra.strftime("%d/%m/%Y") if i.ultima_compra else None
                } for i in itens_inativos
            ],
            "recomendacoes": recomendacoes
        }