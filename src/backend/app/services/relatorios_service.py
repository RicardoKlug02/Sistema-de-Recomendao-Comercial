"""Última compra de cada código na rede, sem misturar preços de fábricas distintas."""
from datetime import date
from sqlalchemy import func
from src.backend.app.models import Cliente, Fabrica, Venda, Produto, ItemVenda


class RelatoriosService:
    def __init__(self, db):
        self.db = db

    def redes(self):
        return [{"nome": nome, "clientes": quantidade} for nome, quantidade in
                self.db.query(Cliente.grupo_economico, func.count(Cliente.id))
                .filter(Cliente.grupo_economico.isnot(None), func.trim(Cliente.grupo_economico) != "")
                .group_by(Cliente.grupo_economico).order_by(Cliente.grupo_economico)]

    def produtos_rede(self, rede, fabrica_id=None):
        clientes = self.db.query(Cliente.id).filter(Cliente.grupo_economico == rede)
        quantidade_clientes = clientes.count()
        if not quantidade_clientes:
            raise ValueError("Rede não encontrada. Confira o cadastro de Rede de clientes nas planilhas.")
        fabrica = self.db.get(Fabrica, fabrica_id) if fabrica_id is not None else None
        if fabrica_id is not None and not fabrica:
            raise ValueError("Fábrica não encontrada.")
        vendas = self.db.query(Venda).filter(Venda.cliente_id.in_(clientes), Venda.data_venda <= date.today())
        if fabrica_id is not None:
            vendas = vendas.filter(Venda.fabrica_id == fabrica_id)
        ordenados = (self.db.query(ItemVenda.produto_id, ItemVenda.preco_unitario,
                    Venda.numero_pedido, Venda.data_venda, Venda.cliente_id,
                    func.row_number().over(partition_by=ItemVenda.produto_id,
                        order_by=(Venda.data_venda.desc(), Venda.id.desc(), ItemVenda.id.desc())).label("posicao"))
                    .join(Venda, Venda.id == ItemVenda.venda_id)
                    .filter(Venda.id.in_(vendas.with_entities(Venda.id))).subquery())
        linhas = (self.db.query(Produto.id, Produto.sku, Produto.nome, Fabrica.nome_fantasia,
                  ordenados.c.data_venda, ordenados.c.preco_unitario, ordenados.c.numero_pedido, Cliente.razao_social)
                  .join(ordenados, ordenados.c.produto_id == Produto.id)
                  .join(Fabrica, Fabrica.id == Produto.fabrica_id)
                  .join(Cliente, Cliente.id == ordenados.c.cliente_id)
                  .filter(ordenados.c.posicao == 1).order_by(Fabrica.nome_fantasia, Produto.sku).all())
        sem_itens = vendas.filter(~Venda.itens.any()).count()
        return {"rede": rede, "fabrica": fabrica.nome_fantasia if fabrica else "Todas as fábricas",
                "clientes": quantidade_clientes, "total": len(linhas), "pedidos_sem_itens": sem_itens,
                "produtos": [{"produto_id": r[0], "sku": r[1], "nome": r[2], "fabrica": r[3],
                    "ultima_compra": r[4].isoformat(), "ultimo_preco": r[5],
                    "pedido": r[6], "cliente": r[7]} for r in linhas]}
