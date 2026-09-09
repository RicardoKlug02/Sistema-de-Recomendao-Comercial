from typing import Any, Dict, List
import pandas as pd
from mlxtend.frequent_patterns import association_rules, fpgrowth
from sqlalchemy.orm import Session

from src.backend.app.models.item_venda import ItemVenda
from src.backend.app.models.produto import Produto
from src.backend.app.models.venda import Venda


class AssociacaoService:

    def __init__(self, db_session: Session):
        self.db = db_session

    def _montar_cesta_pedidos(self) -> pd.DataFrame:
        """Monta a matriz esparsa transacional (Pedido x Produto)."""
        query = (
            self.db.query(
                Venda.numero_pedido,
                Produto.id.label("produto_id"),
            )
            .join(ItemVenda, ItemVenda.venda_id == Venda.id)
            .join(Produto, Produto.id == ItemVenda.produto_id)
            .statement
        )
        df = pd.read_sql(query, self.db.bind)
        if df.empty:
            return pd.DataFrame()

        # Tabela one-hot (True se o produto esteve no pedido)
        cesta = (
            df.groupby(["numero_pedido", "produto_id"])["produto_id"]
            .count()
            .unstack(fill_value=0)
            > 0
        )
        return cesta

    def recomendar_cross_selling(
        self,
        produto_ids: List[int],
        top_n: int = 4,
        min_support: float = 0.01,
        min_confidence: float = 0.2,
    ) -> List[Dict[str, Any]]:
        """Dado um conjunto de itens já adicionados ao orçamento/carrinho,

        recomenda produtos frequentemente levados em conjunto.
        """
        cesta = self._montar_cesta_pedidos()
        if cesta.empty or len(cesta) < 5:
            return []

        # Mineração com FP-Growth
        itens_frequentes = fpgrowth(
            cesta, min_support=min_support, use_colnames=True
        )
        if itens_frequentes.empty:
            return []

        regras = association_rules(
            itens_frequentes, metric="confidence", min_threshold=min_confidence
        )
        if regras.empty:
            return []

        # Filtra regras onde os antecedentes estão no carrinho
        produtos_alvo = set(produto_ids)
        regras_aplicaveis = regras[
            regras["antecedents"].apply(lambda ant: bool(ant.issubset(produtos_alvo)))
        ]

        if regras_aplicaveis.empty:
            return []

        # Ordena por Lift (força do vínculo comercial) e Confiança
        regras_ordenadas = regras_aplicaveis.sort_values(
            by=["lift", "confidence"], ascending=False
        )

        itens_sugeridos_ids = set()
        sugestoes = []

        for _, row in regras_ordenadas.iterrows():
            consequentes = list(row["consequents"])
            for item_id in consequentes:
                if item_id not in produtos_alvo and item_id not in itens_sugeridos_ids:
                    itens_sugeridos_ids.add(item_id)
                    sugestoes.append(
                        {
                            "produto_id": int(item_id),
                            "confianca_pct": round(float(row["confidence"]) * 100, 1),
                            "lift": round(float(row["lift"]), 2),
                        }
                    )
                if len(sugestoes) >= top_n:
                    break
            if len(sugestoes) >= top_n:
                break

        # Metadados
        produtos_db = (
            self.db.query(Produto)
            .filter(Produto.id.in_(list(itens_sugeridos_ids)))
            .all()
        )
        mapa = {p.id: p for p in produtos_db}

        resultado = []
        for s in sugestoes:
            prod = mapa.get(s["produto_id"])
            if prod:
                resultado.append(
                    {
                        "produto_id": prod.id,
                        "sku": prod.sku,
                        "nome": prod.nome,
                        "confianca_pct": s["confianca_pct"],
                        "lift": s["lift"],
                        "motivo": f"Comprado junto em {s['confianca_pct']}% dos pedidos semelhantes",
                    }
                )

        return resultado