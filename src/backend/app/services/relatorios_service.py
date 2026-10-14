from src.backend.app.services.datas import hoje_comercial
"""Última compra de cada código na rede, sem misturar preços de fábricas distintas."""
from datetime import date
from sqlalchemy import func
from src.backend.app.services.identidade_cliente import IdentidadeCliente
from src.backend.app.models import Cliente, Fabrica, Venda, Produto, ItemVenda


class RelatoriosService:
    def __init__(self, db):
        self.db = db

    def redes(self):
        identidade = IdentidadeCliente(self.db)
        grupos = {}
        for cid,c in identidade.clientes.items():
            if (c.grupo_economico or '').strip():
                grupo = identidade.id(cid)
                grupos.setdefault(grupo, {"nome": identidade.nome(cid), "clientes": 0})["clientes"] += 1
        return sorted(grupos.values(), key=lambda r:r['nome'].casefold())

    def produtos_rede(self, rede, fabrica_id=None):
        identidade = IdentidadeCliente(self.db)
        clientes = [cid for cid,c in identidade.clientes.items()
                    if (c.grupo_economico or '').strip().casefold() == rede.strip().casefold()]
        quantidade_clientes = len(clientes)
        if not quantidade_clientes:
            raise ValueError("Rede não encontrada. Confira o cadastro de Rede de clientes nas planilhas.")
        fabrica = self.db.get(Fabrica, fabrica_id) if fabrica_id is not None else None
        if fabrica_id is not None and not fabrica:
            raise ValueError("Fábrica não encontrada.")
        vendas = self.db.query(Venda).filter(Venda.cliente_id.in_(clientes), Venda.data_venda <= hoje_comercial())
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
