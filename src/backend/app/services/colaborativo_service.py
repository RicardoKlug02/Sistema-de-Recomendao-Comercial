from typing import Any, Dict, List
import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy.orm import Session

from src.backend.app.models.item_venda import ItemVenda
from src.backend.app.models.produto import Produto
from src.backend.app.models.venda import Venda


class ColaborativoService:

    def __init__(self, db_session: Session):
        self.db = db_session

    def _montar_matriz_cliente_produto(self) -> pd.DataFrame:
        """Extrai o histórico de vendas e constrói a matriz esparsa Cliente x Produto.

        As linhas são os IDs de clientes e as colunas são os SKUs dos produtos.
        O valor da célula representa o volume total já adquirido pelo cliente.
        """
        query = (
            self.db.query(
                Venda.cliente_id,
                Produto.id.label("produto_id"),
                Produto.sku,
                Produto.nome.label("produto_nome"),
                ItemVenda.quantidade,
            )
            .join(ItemVenda, ItemVenda.venda_id == Venda.id)
            .join(Produto, Produto.id == ItemVenda.produto_id)
            .statement
        )

        df = pd.read_sql(query, self.db.bind)

        if df.empty:
            return pd.DataFrame()

        # Agrupa cliente e produto somando as quantidades
        matriz = (
            df.groupby(["cliente_id", "produto_id"])["quantidade"]
            .sum()
            .unstack(fill_value=0)
        )

        return matriz

    def encontrar_clientes_similares(
        self, cliente_id: int, top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Calcula o grau de afinidade do cliente_id com todos os outros clientes."""
        matriz = self._montar_matriz_cliente_produto()

        if matriz.empty or cliente_id not in matriz.index:
            return []

        # Calcula a similaridade de cosseno entre todas as linhas (clientes)
        sim_matrix = cosine_similarity(matriz.values)
        df_sim = pd.DataFrame(
            sim_matrix, index=matriz.index, columns=matriz.index
        )

        # Extrai os vizinhos mais próximos descartando o próprio cliente
        score_vizinhos = (
            df_sim.loc[cliente_id].drop(index=cliente_id).sort_values(
                ascending=False
            )
        )

        similares = []
        for outro_id, similaridade in score_vizinhos.head(top_k).items():
            if similaridade > 0:
                similares.append(
                    {
                        "cliente_id": int(outro_id),
                        "similaridade": round(float(similaridade) * 100, 2),
                    }
                )

        return similares

    def recomendar_produtos_cliente(
        self,
        cliente_id: int,
        top_k_vizinhos: int = 5,
        top_n_produtos: int = 4,
    ) -> List[Dict[str, Any]]:
        """Gera recomendações de expansão de mix para o cliente_id

        com base no que clientes similares a ele compram e ele ainda não
        adquiriu.
        """
        matriz = self._montar_matriz_cliente_produto()

        if (
            matriz.empty
            or cliente_id not in matriz.index
            or len(matriz.index) < 2
        ):
            return []

        # 1. Similaridade de cosseno entre os clientes
        sim_matrix = cosine_similarity(matriz.values)
        df_sim = pd.DataFrame(
            sim_matrix, index=matriz.index, columns=matriz.index
        )

        # Pega os K clientes mais parecidos com similaridade > 0
        vizinhos = df_sim.loc[cliente_id].drop(index=cliente_id)
        vizinhos = vizinhos[vizinhos > 0].sort_values(ascending=False).head(
            top_k_vizinhos
        )

        if vizinhos.empty:
            return []

        # 2. Identifica o que o cliente alvo já comprou
        produtos_cliente = set(matriz.columns[matriz.loc[cliente_id] > 0])

        # 3. Calcula o score ponderado de recomendação para itens não comprados
        sub_matriz_vizinhos = matriz.loc[vizinhos.index]
        scores_produtos = {}

        for prod_id in matriz.columns:
            # Pula produtos que o cliente já compra
            if prod_id in produtos_cliente:
                continue

            # Quantidades compradas pelos vizinhos
            compras_vizinhos = sub_matriz_vizinhos[prod_id].values
            pesos_similaridade = vizinhos.values

            # Se nenhum dos vizinhos comprou esse item, ignora
            if np.sum(compras_vizinhos) == 0:
                continue

            # Score ponderado pela similaridade dos vizinhos
            score = np.dot(compras_vizinhos, pesos_similaridade) / np.sum(
                pesos_similaridade
            )
            scores_produtos[prod_id] = score

        if not scores_produtos:
            return []

        # 4. Ordena os produtos por relevância
        produtos_ranqueados = sorted(
            scores_produtos.items(), key=lambda x: x[1], reverse=True
        )[:top_n_produtos]

        # 5. Busca metadados dos produtos recomendados
        produtos_ids = [p_id for p_id, _ in produtos_ranqueados]
        produtos_db = (
            self.db.query(Produto).filter(Produto.id.in_(produtos_ids)).all()
        )
        mapa_produtos = {p.id: p for p in produtos_db}

        recomendacoes = []
        for prod_id, score in produtos_ranqueados:
            prod = mapa_produtos.get(prod_id)
            if prod:
                recomendacoes.append(
                    {
                        "produto_id": prod.id,
                        "sku": prod.sku,
                        "nome": prod.nome,
                        "score_relevancia": round(float(score), 2),
                        "motivo": f"Comprado por clientes com histórico de compras similar",
                    }
                )

        return recomendacoes