from datetime import date, timedelta
from typing import Any, Dict, List
import numpy as np
import pandas as pd
from sqlalchemy.orm import Session

from src.backend.app.core.security import decrypt_data
from src.backend.app.models.cliente import Cliente
from src.backend.app.models.fabrica import Fabrica
from src.backend.app.models.item_venda import ItemVenda
from src.backend.app.models.produto import Produto
from src.backend.app.models.venda import Venda
from src.backend.app.services.colaborativo_service import ColaborativoService


class ClienteDossieService:

    def __init__(self, db_session: Session):
        self.db = db_session
        self.colaborativo = ColaborativoService(db_session=db_session)

    def gerar_dossie_completo(
        self, cliente_id: int, ref_date: date = None
    ) -> Dict[str, Any]:
        ref = ref_date or date.today()

        # 1. Carrega dados cadastrais do cliente
        cliente = (
            self.db.query(Cliente).filter(Cliente.id == cliente_id).first()
        )
        if not cliente:
            raise ValueError("Cliente não encontrado.")

        # 2. Carrega histórico de compras com joins explícitos
        query = (
            self.db.query(
                Venda.id.label("venda_id"),
                Fabrica.nome_fantasia.label("fabrica"),
                Venda.data_venda,
                Venda.valor_total,
                ItemVenda.produto_id,
                ItemVenda.quantidade,
                Produto.sku,
                Produto.nome.label("produto_nome"),
            )
            .join(ItemVenda, ItemVenda.venda_id == Venda.id)
            .join(Produto, Produto.id == ItemVenda.produto_id)
            .join(Fabrica, Fabrica.id == Venda.fabrica_id)
            .filter(Venda.cliente_id == cliente_id)
        )

        df = pd.read_sql(query.statement, self.db.bind)

        # Se não comprou por Venda.fabrica_id, testa a ligação por Produto.fabrica_id
        if df.empty:
            query_alt = (
                self.db.query(
                    Venda.id.label("venda_id"),
                    Fabrica.nome_fantasia.label("fabrica"),
                    Venda.data_venda,
                    Venda.valor_total,
                    ItemVenda.produto_id,
                    ItemVenda.quantidade,
                    Produto.sku,
                    Produto.nome.label("produto_nome"),
                )
                .join(ItemVenda, ItemVenda.venda_id == Venda.id)
                .join(Produto, Produto.id == ItemVenda.produto_id)
                .join(Fabrica, Fabrica.id == Produto.fabrica_id)
                .filter(Venda.cliente_id == cliente_id)
            )
            df = pd.read_sql(query_alt.statement, self.db.bind)

        if df.empty:
            return {
                "cliente_id": cliente.id,
                "razao_social": decrypt_data(cliente.razao_social)
                if cliente.razao_social
                else "N/D",
                "mensagem": "Cliente sem registros de vendas para análise.",
            }

        df["data_venda"] = pd.to_datetime(df["data_venda"]).dt.date
        df["valor_total"] = df["valor_total"].astype(float)
        df["quantidade"] = df["quantidade"].astype(float)

        return {
            "cliente_id": cliente.id,
            "razao_social": decrypt_data(cliente.razao_social)
            if cliente.razao_social
            else "N/D",
            "grupo_economico": getattr(cliente, "grupo_economico", None),
            "resumo_fabricas": self._analisar_fabricas(df, ref),
            "sugestoes_reposicao": self._analisar_reposicao(df, ref),
            "produtos_em_abandono": self._analisar_produtos_abandono(df, ref),
            "performance_yoy": self._analisar_yoy(df, ref),
            "sugestoes_expansao_mix": self.colaborativo.recomendar_produtos_cliente(
                cliente_id, top_n_produtos=4
            ),
        }

    def _analisar_fabricas(
        self, df: pd.DataFrame, ref: date
    ) -> List[Dict[str, Any]]:
        status_fabricas = []
        for fabrica, dados in df.groupby("fabrica"):
            pedidos = (
                dados[["venda_id", "data_venda", "valor_total"]]
                .drop_duplicates()
                .sort_values("data_venda")
            )
            datas = pedidos["data_venda"].tolist()
            ultima_compra = datas[-1]
            dias_parado = (ref - ultima_compra).days

            if len(datas) > 1:
                intervalos = [
                    (datas[i] - datas[i - 1]).days
                    for i in range(1, len(datas))
                ]
                ciclo_medio = int(np.mean(intervalos))
            else:
                ciclo_medio = 90

            limite_90d = ultima_compra + timedelta(days=90)

            status = "Ativo"
            if dias_parado >= 90:
                status = "Inativo na Fábrica"
            elif dias_parado > ciclo_medio:
                status = "Ciclo Atrasado"

            status_fabricas.append(
                {
                    "fabrica": fabrica,
                    "ultima_compra": ultima_compra.strftime("%d/%m/%Y"),
                    "dias_sem_comprar": dias_parado,
                    "ciclo_medio_dias": ciclo_medio,
                    "data_limite_inatividade": limite_90d.strftime("%d/%m/%Y"),
                    "status": status,
                    "risco_bloqueio_neste_mes": (
                        limite_90d.month == ref.month
                        and limite_90d.year == ref.year
                    ),
                }
            )
        return status_fabricas

    def _analisar_reposicao(
        self, df: pd.DataFrame, ref: date
    ) -> List[Dict[str, Any]]:
        sugestoes = []
        for prod_id, dados in df.groupby("produto_id"):
            compras = dados.sort_values("data_venda")
            datas = compras["data_venda"].tolist()
            if len(datas) < 2:
                continue

            intervalos = [
                (datas[i] - datas[i - 1]).days for i in range(1, len(datas))
            ]
            ciclo = int(np.mean(intervalos))
            ultima = datas[-1]
            atraso = (ref - ultima).days - ciclo

            # Alerta: até 5 dias antes da data média ou em atraso de até 2 ciclos
            if atraso >= -5 and (ref - ultima).days < (ciclo * 2):
                sugestoes.append(
                    {
                        "sku": compras["sku"].iloc[0],
                        "nome": compras["produto_nome"].iloc[0],
                        "ciclo_medio": ciclo,
                        "dias_desde_ultima": (ref - ultima).days,
                        "status": "Reposição Atrasada"
                        if atraso > 0
                        else "Janela Ideal",
                        "volume_habitual": round(
                            float(compras["quantidade"].mean()), 0
                        ),
                    }
                )
        return sugestoes

    def _analisar_produtos_abandono(
        self, df: pd.DataFrame, ref: date
    ) -> List[Dict[str, Any]]:
        abandonados = []
        for prod_id, dados in df.groupby("produto_id"):
            compras = dados.sort_values("data_venda")
            datas = compras["data_venda"].tolist()
            if len(datas) < 3:
                continue

            intervalos = [
                (datas[i] - datas[i - 1]).days for i in range(1, len(datas))
            ]
            ciclo = int(np.mean(intervalos))
            dias_sem_comprar = (ref - datas[-1]).days

            if (
                dias_sem_comprar > (ciclo * 2.5)
                and dias_sem_comprar >= 60
            ):
                abandonados.append(
                    {
                        "sku": compras["sku"].iloc[0],
                        "nome": compras["produto_nome"].iloc[0],
                        "dias_parado": dias_sem_comprar,
                        "ciclo_habitual": ciclo,
                        "total_vezes_comprado": len(datas),
                    }
                )
        return abandonados

    def _analisar_yoy(
        self, df: pd.DataFrame, ref: date
    ) -> Dict[str, Any]:
        mes_atual = ref.month - 1 if ref.month > 1 else 12
        ano_atual = ref.year if ref.month > 1 else ref.year - 1
        ano_passado = ano_atual - 1

        pedidos = df[
            ["venda_id", "data_venda", "valor_total"]
        ].drop_duplicates()
        pedidos["data_dt"] = pd.to_datetime(pedidos["data_venda"])
        pedidos["ano"] = pedidos["data_dt"].dt.year
        pedidos["mes"] = pedidos["data_dt"].dt.month

        fat_recente = pedidos[
            (pedidos["ano"] == ano_atual) & (pedidos["mes"] == mes_atual)
        ]["valor_total"].sum()

        fat_anterior = pedidos[
            (pedidos["ano"] == ano_passado)
            & (pedidos["mes"] == mes_atual)
        ]["valor_total"].sum()

        variacao = (
            ((fat_recente - fat_anterior) / fat_anterior * 100)
            if fat_anterior > 0
            else 0.0
        )

        return {
            "periodo_recente": f"{mes_atual:02d}/{ano_atual}",
            "periodo_comparado": f"{mes_atual:02d}/{ano_passado}",
            "faturamento_recente": round(float(fat_recente), 2),
            "faturamento_ano_anterior": round(float(fat_anterior), 2),
            "crescimento_pct": round(float(variacao), 2),
        }