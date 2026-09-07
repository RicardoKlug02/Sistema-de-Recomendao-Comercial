from datetime import date, datetime
from typing import Any, Dict, List
import numpy as np
import pandas as pd
from sqlalchemy.orm import Session

from src.backend.app.models.cliente import Cliente
from src.backend.app.models.item_venda import ItemVenda
from src.backend.app.models.produto import Produto
from src.backend.app.models.venda import Venda


class RecompraService:

    def __init__(self, db_session: Session):
        self.db = db_session

    def _carregar_historico_compras(
        self, cliente_id: int = None
    ) -> pd.DataFrame:
        """Carrega transações com datas para análise de periodicidade."""
        query = (
            self.db.query(
                Venda.cliente_id,
                Venda.data_venda,
                Produto.id.label("produto_id"),
                Produto.sku,
                Produto.nome.label("produto_nome"),
                ItemVenda.quantidade,
            )
            .join(ItemVenda, ItemVenda.venda_id == Venda.id)
            .join(Produto, Produto.id == ItemVenda.produto_id)
        )

        if cliente_id:
            query = query.filter(Venda.cliente_id == cliente_id)

        df = pd.read_sql(query.statement, self.db.bind)

        if not df.empty:
            df["data_venda"] = pd.to_datetime(df["data_venda"])

        return df

    def analisar_oportunidades_cliente(
        self,
        cliente_id: int,
        data_referencia: date = None,
        margem_tolerancia_dias: int = 5,
    ) -> List[Dict[str, Any]]:
        """Calcula o ciclo de reposição por produto para um cliente específico."""
        df = self._carregar_historico_compras(cliente_id=cliente_id)

        if df.empty:
            return []

        hoje = pd.to_datetime(data_referencia or date.today())
        oportunidades = []

        # Agrupa por produto para calcular o ciclo de recompra de cada um
        for (prod_id, sku, nome), grupo in df.groupby(
            ["produto_id", "sku", "produto_nome"]
        ):
            # Ordena as datas de compra do produto
            datas = (
                grupo["data_venda"].drop_duplicates().sort_values().tolist()
            )
            qtd_compras = len(datas)

            # Caso 1: Comprou apenas 1 vez (não há ciclo histórico calculado)
            if qtd_compras < 2:
                ultima_compra = datas[-1]
                dias_desde_ultima = (hoje - ultima_compra).days

                # Se já comprou há mais de 45 dias, sinaliza como reativação
                if dias_desde_ultima >= 45:
                    oportunidades.append(
                        {
                            "produto_id": int(prod_id),
                            "sku": sku,
                            "produto": nome,
                            "tipo_alerta": "Compra Única - Reativação",
                            "ciclo_medio_dias": None,
                            "dias_desde_ultima_compra": dias_desde_ultima,
                            "dias_atraso": None,
                            "data_ultima_compra": ultima_compra.strftime(
                                "%Y-%m-%d"
                            ),
                            "urgencia": "Média",
                        }
                    )
                continue

            # Caso 2: Comprou 2 ou mais vezes (calcula a média de dias entre compras)
            diferencas = [
                (datas[i] - datas[i - 1]).days for i in range(1, len(datas))
            ]
            ciclo_medio = float(np.mean(diferencas))

            ultima_compra = datas[-1]
            dias_desde_ultima = (hoje - ultima_compra).days
            data_prevista = ultima_compra + pd.Timedelta(days=ciclo_medio)
            dias_atraso = dias_desde_ultima - int(ciclo_medio)

            # Só sugere se já estiver na janela de recompra (dentro da margem ou atrasado)
            if dias_desde_ultima >= (ciclo_medio - margem_tolerancia_dias):
                if dias_atraso > 15:
                    urgencia = "Crítica (Risco de Churn)"
                elif dias_atraso > 0:
                    urgencia = "Alta (Vencido)"
                else:
                    urgencia = "Oportunidade (Janela Aberta)"

                oportunidades.append(
                    {
                        "produto_id": int(prod_id),
                        "sku": sku,
                        "produto": nome,
                        "tipo_alerta": "Reposição Recorrente",
                        "total_compras_historico": qtd_compras,
                        "ciclo_medio_dias": round(ciclo_medio, 1),
                        "dias_desde_ultima_compra": dias_desde_ultima,
                        "dias_atraso": dias_atraso,
                        "data_ultima_compra": ultima_compra.strftime(
                            "%Y-%m-%d"
                        ),
                        "data_prevista_recompra": data_prevista.strftime(
                            "%Y-%m-%d"
                        ),
                        "urgencia": urgencia,
                    }
                )

        # Ordena priorizando os produtos com maior atraso
        oportunidades.sort(
            key=lambda x: (
                x.get("dias_atraso") is not None,
                x.get("dias_atraso", 0),
            ),
            reverse=True,
        )

        return oportunidades

    def listar_clientes_em_risco(
        self, limite_dias_sem_comprar: int = 60
    ) -> List[Dict[str, Any]]:
        """Varre todos os clientes e lista aqueles que pararam de comprar qualquer produto."""
        query = (
            self.db.query(
                Cliente.id.label("cliente_id"),
                Cliente.razao_social,
                Cliente.cnpj_cpf,
                Venda.data_venda,
            )
            .join(Venda, Venda.cliente_id == Cliente.id)
            .statement
        )

        df = pd.read_sql(query, self.db.bind)
        if df.empty:
            return []

        df["data_venda"] = pd.to_datetime(df["data_venda"])
        hoje = pd.to_datetime(date.today())

        clientes_inativos = []
        for (c_id, razao, cnpj), grupo in df.groupby(
            ["cliente_id", "razao_social", "cnpj_cpf"]
        ):
            ultima_venda = grupo["data_venda"].max()
            dias_inativo = (hoje - ultima_venda).days

            if dias_inativo >= limite_dias_sem_comprar:
                clientes_inativos.append(
                    {
                        "cliente_id": int(c_id),
                        "razao_social": razao,
                        "cnpj_cpf": cnpj,
                        "dias_inativo": dias_inativo,
                        "ultima_compra": ultima_venda.strftime("%Y-%m-%d"),
                    }
                )

        clientes_inativos.sort(key=lambda x: x["dias_inativo"], reverse=True)
        return clientes_inativos