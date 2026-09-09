from datetime import date, timedelta
from typing import Any, Dict, List, Optional
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

    def _obter_identificador_grupo(self, cliente_id: int) -> str:
        cliente = (
            self.db.query(Cliente.grupo_economico, Cliente.cnpj_cpf)
            .filter(Cliente.id == cliente_id)
            .first()
        )
        if not cliente:
            return ""
        return cliente.grupo_economico or cliente.cnpj_cpf

    def _carregar_historico_cliente_ou_grupo(
        self, cliente_id: int
    ) -> pd.DataFrame:
        """Carrega todas as compras realizadas pelo grupo econômico do cliente,

        garantindo visão consolidada entre matriz e filiais.
        """
        grupo_alvo = self._obter_identificador_grupo(cliente_id)
        if not grupo_alvo:
            return pd.DataFrame()

        query = (
            self.db.query(
                Venda.data_venda,
                Produto.id.label("produto_id"),
                Produto.sku,
                Produto.nome.label("produto_nome"),
                ItemVenda.quantidade,
            )
            .join(Cliente, Cliente.id == Venda.cliente_id)
            .join(ItemVenda, ItemVenda.venda_id == Venda.id)
            .join(Produto, Produto.id == ItemVenda.produto_id)
            .filter(
                (Cliente.grupo_economico == grupo_alvo)
                | (Cliente.cnpj_cpf == grupo_alvo)
            )
            .order_by(Venda.data_venda.asc())
            .statement
        )

        df = pd.read_sql(query, self.db.bind)
        if not df.empty:
            df["data_venda"] = pd.to_datetime(df["data_venda"])
        return df

    def obter_alertas_globais_alto_volume(
        self,
        percentil_volume: float = 0.70,
        limite_alertas: int = 10,
        data_referencia: Optional[date] = None,
    ) -> List[Dict[str, Any]]:
        """Varre toda a base para a tela inicial, identificando produtos de alto volume

        que estão com a recompra atrasada ou em risco de churn.
        """
        # 1. Carrega todas as vendas consolidadas com identificador do grupo/cliente
        query = (
            self.db.query(
                Cliente.id.label("cliente_id"),
                Cliente.razao_social,
                Cliente.grupo_economico,
                Cliente.cnpj_cpf,
                Produto.id.label("produto_id"),
                Produto.sku,
                Produto.nome.label("produto_nome"),
                Venda.data_venda,
                ItemVenda.quantidade,
            )
            .join(Cliente, Cliente.id == Venda.cliente_id)
            .join(ItemVenda, ItemVenda.venda_id == Venda.id)
            .join(Produto, Produto.id == ItemVenda.produto_id)
            .order_by(Venda.data_venda.asc())
            .statement
        )

        df = pd.read_sql(query, self.db.bind)
        if df.empty:
            return []

        df["data_venda"] = pd.to_datetime(df["data_venda"])
        df["grupo_analitico"] = df["grupo_economico"].fillna(df["cnpj_cpf"])

        ponto_corte = (
            pd.to_datetime(data_referencia)
            if data_referencia
            else df["data_venda"].max()
        )

        # 2. Define o limiar de alto volume na carteira
        corte_qtd = df["quantidade"].quantile(percentil_volume)

        alertas_globais = []

        # Agrupa por cliente/grupo e produto
        for (grupo, prod_id), group in df.groupby(
            ["grupo_analitico", "produto_id"]
        ):
            datas_unicas = sorted(
                group["data_venda"].drop_duplicates().tolist()
            )
            if len(datas_unicas) < 2:
                continue

            vol_medio = group["quantidade"].mean()
            # Filtra apenas itens com saída relevante (alto volume)
            if vol_medio < corte_qtd:
                continue

            intervalos = [
                (datas_unicas[i] - datas_unicas[i - 1]).days
                for i in range(1, len(datas_unicas))
            ]
            periodicidade = float(np.mean(intervalos))
            ultima_compra = datas_unicas[-1]
            dias_desde_ultima = (ponto_corte - ultima_compra).days
            dias_esperados = int(round(periodicidade))
            dias_atraso = dias_desde_ultima - dias_esperados

            # Apenas itens em atraso ou risco de churn
            if dias_atraso > 5:
                status = (
                    "Risco Crítico de Churn"
                    if dias_atraso > (dias_esperados * 1.5)
                    else "Atrasado"
                )
                cliente_ref = group.iloc[0]

                alertas_globais.append(
                    {
                        "cliente_id": int(cliente_ref["cliente_id"]),
                        "razao_social_raw": cliente_ref["razao_social"],
                        "grupo_economico": grupo,
                        "produto_id": int(prod_id),
                        "sku": cliente_ref["sku"],
                        "nome_produto": cliente_ref["produto_nome"],
                        "volume_medio_pedido": int(round(vol_medio)),
                        "periodicidade_dias": round(periodicidade, 1),
                        "dias_atraso": dias_atraso,
                        "status": status,
                    }
                )

        # Ordena pelos atrasos mais críticos e maiores volumes
        alertas_globais.sort(
            key=lambda x: (x["status"] == "Risco Crítico de Churn", x["dias_atraso"] * x["volume_medio_pedido"]),
            reverse=True,
        )

        return alertas_globais[:limite_alertas]

    def analisar_oportunidades_cliente(
        self,
        cliente_id: int,
        data_referencia: Optional[date] = None,
        margem_tolerancia_dias: int = 5,
    ) -> List[Dict[str, Any]]:
        """Gera a lista de produtos com periodicidade mapeada e seus status de reposição."""
        df = self._carregar_historico_cliente_ou_grupo(cliente_id=cliente_id)

        if df.empty:
            return []

        # Data de corte: usa data_referencia ou a maior data registrada no histórico do banco
        if data_referencia:
            ponto_corte = pd.to_datetime(data_referencia)
        else:
            ponto_corte = df["data_venda"].max()

        oportunidades = []

        # Analisa o histórico de cada produto individualmente
        for produto_id, group in df.groupby("produto_id"):
            datas_unicas = sorted(group["data_venda"].drop_duplicates().tolist())
            total_compras = len(datas_unicas)

            # Só conseguimos calcular periodicidade se o cliente comprou pelo menos 2 vezes em datas diferentes
            if total_compras < 2:
                continue

            # Calcula intervalos em dias entre as compras consecutivas
            intervalos = [
                (datas_unicas[i] - datas_unicas[i - 1]).days
                for i in range(1, len(datas_unicas))
            ]
            periodicidade_media = float(np.mean(intervalos))

            # Dados da última compra
            ultima_compra = datas_unicas[-1]
            dias_desde_ultima = (ponto_corte - ultima_compra).days

            # Previsão da próxima compra e atraso
            dias_esperados = int(round(periodicidade_media))
            data_prevista = (ultima_compra + timedelta(days=dias_esperados)).date()
            dias_atraso = dias_desde_ultima - dias_esperados

            # Classificação de status
            if dias_atraso > (dias_esperados * 1.5):
                status = "Risco Crítico de Churn"
                nivel_prioridade = 1
            elif dias_atraso > margem_tolerancia_dias:
                status = "Atrasado (Reposição Necessária)"
                nivel_prioridade = 2
            elif abs(dias_atraso) <= margem_tolerancia_dias:
                status = "Oportunidade (Janela Ideal de Compra)"
                nivel_prioridade = 3
            else:
                status = "Em Dia"
                nivel_prioridade = 4

            # Só adiciona itens que são acionáveis comercialmente (descarta 'Em Dia' se quiser focar em alertas)
            sku = group["sku"].iloc[0]
            nome = group["produto_nome"].iloc[0]
            media_volume = int(round(group["quantidade"].mean()))

            oportunidades.append(
                {
                    "produto_id": int(produto_id),
                    "sku": sku,
                    "nome": nome,
                    "total_compras_historico": total_compras,
                    "dias_desde_ultima_compra": dias_desde_ultima,
                    "periodicidade_media_dias": round(periodicidade_media, 1),
                    "previsao_proxima_compra": data_prevista,
                    "dias_atraso": max(0, dias_atraso),
                    "volume_medio_pedido": media_volume,
                    "status": status,
                    "prioridade": nivel_prioridade,
                }
            )

        # Ordena priorizando quem está em risco crítico e atraso maior
        oportunidades_ordenadas = sorted(
            oportunidades,
            key=lambda x: (x["prioridade"], -x["dias_atraso"]),
        )

        return oportunidades_ordenadas