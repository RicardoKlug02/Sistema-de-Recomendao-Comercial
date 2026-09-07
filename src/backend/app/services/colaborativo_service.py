from typing import Any, Dict, List
import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy.orm import Session

from src.backend.app.models.cliente import Cliente
from src.backend.app.models.item_venda import ItemVenda
from src.backend.app.models.produto import Produto
from src.backend.app.models.venda import Venda


class ColaborativoService:

    def __init__(self, db_session: Session):
        self.db = db_session

    def _obter_identificador_grupo(self, cliente_id: int) -> str:
        """Retorna o grupo_economico do cliente ou o próprio cnpj_cpf se for isolado."""
        cliente = (
            self.db.query(Cliente.grupo_economico, Cliente.cnpj_cpf)
            .filter(Cliente.id == cliente_id)
            .first()
        )
        if not cliente:
            return ""
        return cliente.grupo_economico or cliente.cnpj_cpf

    def _montar_matriz_grupo_produto(self) -> pd.DataFrame:
        """Constrói a matriz Grupo Econômico x Produto.

        Linhas: Identificador consolidado do Grupo Econômico / Rede.
        Colunas: ID do Produto.
        Valores: Volume total acumulado comprado por todas as filiais daquele grupo.
        """
        query = (
            self.db.query(
                Cliente.grupo_economico,
                Cliente.cnpj_cpf,
                Produto.id.label("produto_id"),
                ItemVenda.quantidade,
            )
            .join(Venda, Venda.cliente_id == Cliente.id)
            .join(ItemVenda, ItemVenda.venda_id == Venda.id)
            .join(Produto, Produto.id == ItemVenda.produto_id)
            .statement
        )

        df = pd.read_sql(query, self.db.bind)

        if df.empty:
            return pd.DataFrame()

        # Se grupo_economico for nulo, faz fallback para o cnpj_cpf do cliente
        df["grupo_analitico"] = df["grupo_economico"].fillna(df["cnpj_cpf"])

        # Agrupa por Grupo Econômico e Produto, somando as quantidades de todas as filiais
        matriz = (
            df.groupby(["grupo_analitico", "produto_id"])["quantidade"]
            .sum()
            .unstack(fill_value=0)
        )

        return matriz

    def encontrar_grupos_similares(
        self, cliente_id: int, top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Identifica quais redes/grupos econômicos compram produtos similares ao do cliente informado."""
        grupo_alvo = self._obter_identificador_grupo(cliente_id)
        matriz = self._montar_matriz_grupo_produto()

        if matriz.empty or not grupo_alvo or grupo_alvo not in matriz.index:
            return []

        # Calcula a similaridade de cosseno entre todas as redes
        sim_matrix = cosine_similarity(matriz.values)
        df_sim = pd.DataFrame(
            sim_matrix, index=matriz.index, columns=matriz.index
        )

        score_vizinhos = (
            df_sim.loc[grupo_alvo].drop(index=grupo_alvo).sort_values(
                ascending=False
            )
        )

        similares = []
        for grupo, similaridade in score_vizinhos.head(top_k).items():
            if similaridade > 0:
                similares.append(
                    {
                        "grupo_economico": grupo,
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
        """Gera recomendações com nota percentual de aderência (0-100%)

        e sugestão de volume estimado de compra.
        """
        grupo_alvo = self._obter_identificador_grupo(cliente_id)
        matriz = self._montar_matriz_grupo_produto()

        if (
            matriz.empty
            or not grupo_alvo
            or grupo_alvo not in matriz.index
            or len(matriz.index) < 2
        ):
            return []

        # 1. Identifica os vizinhos mais similares via Cosseno
        sim_matrix = cosine_similarity(matriz.values)
        df_sim = pd.DataFrame(
            sim_matrix, index=matriz.index, columns=matriz.index
        )

        vizinhos = df_sim.loc[grupo_alvo].drop(index=grupo_alvo)
        vizinhos = vizinhos[vizinhos > 0].sort_values(ascending=False).head(
            top_k_vizinhos
        )

        if vizinhos.empty:
            return []

        # 2. Produtos que qualquer filial do grupo já comprou
        produtos_grupo = set(matriz.columns[matriz.loc[grupo_alvo] > 0])

        sub_matriz_vizinhos = matriz.loc[vizinhos.index]
        pesos_similaridade = vizinhos.values
        soma_pesos = np.sum(pesos_similaridade)

        produtos_avaliados = []

        for prod_id in matriz.columns:
            if prod_id in produtos_grupo:
                continue

            compras_vizinhos = sub_matriz_vizinhos[prod_id].values

            # Se nenhum vizinho comprou, descarta
            if np.sum(compras_vizinhos) == 0:
                continue

            # Métrica A: Percentual de Afinidade / Confiança (0% a 100%)
            # Analisa o consenso: quão forte é a adoção desse item entre os similares
            vizinhos_que_compraram = (compras_vizinhos > 0).astype(int)
            afinidade_pct = (
                np.dot(vizinhos_que_compraram, pesos_similaridade) / soma_pesos
            ) * 100

            # Métrica B: Volume Sugerido (Média ponderada do que os vizinhos compram)
            # Calculada apenas sobre quem efetivamente compra para não subestimar lote
            vizinhos_ativos = compras_vizinhos > 0
            if np.any(vizinhos_ativos):
                volume_estimado = np.dot(
                    compras_vizinhos[vizinhos_ativos],
                    pesos_similaridade[vizinhos_ativos],
                ) / np.sum(pesos_similaridade[vizinhos_ativos])
            else:
                volume_estimado = 0.0

            produtos_avaliados.append(
                {
                    "produto_id": prod_id,
                    "afinidade_pct": round(float(afinidade_pct), 1),
                    "volume_sugerido": int(np.ceil(volume_estimado)),
                }
            )

        if not produtos_avaliados:
            return []

        # 3. Ordena pela nota de afinidade (%) e desempata pelo volume sugerido
        produtos_ranqueados = sorted(
            produtos_avaliados,
            key=lambda x: (x["afinidade_pct"], x["volume_sugerido"]),
            reverse=True,
        )[:top_n_produtos]

        # 4. Busca metadados dos produtos
        produtos_ids = [p["produto_id"] for p in produtos_ranqueados]
        produtos_db = (
            self.db.query(Produto).filter(Produto.id.in_(produtos_ids)).all()
        )
        mapa_produtos = {p.id: p for p in produtos_db}

        recomendacoes = []
        for item in produtos_ranqueados:
            prod = mapa_produtos.get(item["produto_id"])
            if prod:
                # Classificação em nota/estrelas para a UI
                nota = item["afinidade_pct"]
                if nota >= 80:
                    status = "Altíssima Aderência"
                elif nota >= 50:
                    status = "Aderência Moderada"
                else:
                    status = "Oportunidade Complementar"

                recomendacoes.append(
                    {
                        "produto_id": prod.id,
                        "sku": prod.sku,
                        "nome": prod.nome,
                        "afinidade_percentual": item["afinidade_pct"],
                        "classificacao": status,
                        "volume_sugerido_unidades": item["volume_sugerido"],
                        "motivo": f"Comprado por {item['afinidade_pct']}% dos clientes de perfil similar",
                    }
                )

        return recomendacoes