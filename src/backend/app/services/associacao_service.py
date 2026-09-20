from collections import defaultdict
from typing import Any, Dict, List, Set
from sqlalchemy.orm import Session

from src.backend.app.models.item_venda import ItemVenda
from src.backend.app.models.produto import Produto
from src.backend.app.models.venda import Venda


class AssociacaoService:

    def __init__(self, db_session: Session):
        self.db = db_session

    def _carregar_cestas_pedidos(self) -> List[Set[int]]:
        """Mapeia os produtos faturados em cada pedido."""
        registros = (
            self.db.query(Venda.id, ItemVenda.produto_id)
            .join(ItemVenda, ItemVenda.venda_id == Venda.id)
            .all()
        )

        cestas_map: Dict[int, Set[int]] = defaultdict(set)
        for venda_id, produto_id in registros:
            cestas_map[venda_id].add(produto_id)

        return [itens for itens in cestas_map.values() if len(itens) >= 2]

    def recomendar_cross_selling(
        self,
        produto_ids: List[int],
        top_n: int = 4,
        min_confidence: float = 0.20,
    ) -> List[Dict[str, Any]]:
        """Sugere produtos para cross-selling via cálculo exato de Confiança e Lift."""
        if not produto_ids:
            return []

        cestas = self._carregar_cestas_pedidos()
        total_pedidos = len(cestas)
        if total_pedidos < 5:
            return []

        alvo_set = set(produto_ids)
        pedidos_com_antecedente = 0
        frequencia_individual: Dict[int, int] = defaultdict(int)
        coocorrencias: Dict[int, int] = defaultdict(int)

        for cesta in cestas:
            for item in cesta:
                frequencia_individual[item] += 1

            if alvo_set & cesta:
                pedidos_com_antecedente += 1
                for item in cesta:
                    if item not in alvo_set:
                        coocorrencias[item] += 1

        if pedidos_com_antecedente == 0 or not coocorrencias:
            return []

        regras = []
        for prod_id, contagem_conjunta in coocorrencias.items():
            confianca = contagem_conjunta / pedidos_com_antecedente
            if confianca < min_confidence:
                continue

            suporte_consequente = frequencia_individual[prod_id] / total_pedidos
            lift = (confianca / suporte_consequente) if suporte_consequente > 0 else 0.0

            if lift > 1.0:
                regras.append({
                    "produto_id": prod_id,
                    "confianca_pct": round(confianca * 100, 1),
                    "lift": round(lift, 2),
                })

        regras.sort(key=lambda x: (x["lift"], x["confianca_pct"]), reverse=True)
        top_regras = regras[:top_n]

        if not top_regras:
            return []

        ids_sugeridos = [r["produto_id"] for r in top_regras]
        produtos_db = {
            p.id: p
            for p in self.db.query(Produto).filter(Produto.id.in_(ids_sugeridos)).all()
        }

        resultado = []
        for r in top_regras:
            prod = produtos_db.get(r["produto_id"])
            if not prod:
                continue

            resultado.append({
                "produto_id": prod.id,
                "sku": prod.sku,
                "nome": prod.nome,
                "confianca_pct": r["confianca_pct"],
                "lift": r["lift"],
                "motivo": f"Comprado junto em {r['confianca_pct']}% dos pedidos semelhantes (Lift: {r['lift']}x)",
            })

        return resultado