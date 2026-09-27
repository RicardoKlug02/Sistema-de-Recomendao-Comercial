from datetime import date, datetime, timedelta
import json
from typing import Any, Dict, List
import pandas as pd
from sqlalchemy.orm import Session

from src.backend.app.models.cliente_analises import (
    AlertaComercial,
    ClienteAnalytics,
    FabricaAnalytics,
    ResumoVendasGeral,
)
from src.backend.app.models.cliente import Cliente
from src.backend.app.models.item_venda import ItemVenda
from src.backend.app.models.produto import Produto
from src.backend.app.models.venda import Venda
from src.backend.app.models.vendedor import Vendedor


class AnalyticsCalculatorService:

    def __init__(self, db_session: Session):
        self.db = db_session

    def processar_tudo(self):
        """Orquestra o recálculo de todas as tabelas analíticas pós-importação."""
        try:
            # Limpa os resumos antigos para recalcular do zero (Clean & Rebuild)
            self._limpar_tabelas_analytics()

            # Executa os pipelines de agregação
            self._processar_resumo_vendas_geral()
            self._processar_cliente_analytics()
            self._processar_fabrica_analytics()
            self._processar_alertas_comerciais()

            self.db.commit()
            return {"status": "sucesso", "mensagem": "Pré-cálculo analítico concluído com sucesso."}
        except Exception as e:
            self.db.rollback()
            raise RuntimeError(f"Erro ao processar o pipeline analítico: {str(e)}")

    def _limpar_tabelas_analytics(self):
        self.db.query(ResumoVendasGeral).delete()
        self.db.query(ClienteAnalytics).delete()
        self.db.query(FabricaAnalytics).delete()
        self.db.query(AlertaComercial).delete()
        self.db.flush()

    def _processar_resumo_vendas_geral(self):
        """Agrupa vendas por Mês, Região Imediata (micro_regiao) e Vendedor."""
        vendas = self.db.query(Venda, Cliente, Vendedor).join(Cliente, Venda.cliente_id == Cliente.id, isouter=True).join(Vendedor, Venda.vendedor_id == Vendedor.id, isouter=True).all()

        if not vendas:
            return

        dados = []
        for venda, cliente, vendedor in vendas:
            if not venda.data_venda:
                continue
            ano_mes = venda.data_venda.strftime("%Y-%m")
            regiao = cliente.micro_regiao if cliente and cliente.micro_regiao else "DESCONHECIDA"
            vendedor_id = vendedor.id if vendedor else None
            fabrica_id = venda.fabrica_id

            dados.append({
                "ano_mes": ano_mes,
                "regiao_imediata": regiao,
                "vendedor_id": vendedor_id,
                "fabrica_id": fabrica_id,
                "valor": venda.valor_total or 0.0,
            })

        df = pd.DataFrame(dados)
        if df.empty:
            return

        # Agrupamento com Pandas para alta performance antes de salvar
        agrupado = df.groupby(["ano_mes", "regiao_imediata", "vendedor_id", "fabrica_id"]).agg(
            total_vendas=("valor", "sum"),
            quantidade_pedidos=("valor", "count"),
        ).reset_index()

        for _, row in agrupado.iterrows():
            ticket_medio = row["total_vendas"] / row["quantidade_pedidos"] if row["quantidade_pedidos"] > 0 else 0.0
            item = ResumoVendasGeral(
                ano_mes=row["ano_mes"],
                regiao_imediata=row["regiao_imediata"],
                vendedor_id=row["vendedor_id"],
                fabrica_id=row["fabrica_id"],
                total_vendas=row["total_vendas"],
                quantidade_pedidos=int(row["quantidade_pedidos"]),
                ticket_medio=ticket_medio,
            )
            self.db.add(item)
        self.db.flush()

    def _processar_cliente_analytics(self):
        """Gera o Raio-X completo 360º por cliente."""
        clientes = self.db.query(Cliente).all()
        hoje = date.today()
        limite_6m = hoje - timedelta(days=180)
        limite_1m_inicio = (hoje.replace(day=1) - timedelta(days=1)).replace(day=1) # Mês anterior fechado

        for cliente in clientes:
            vendas_cliente = self.db.query(Venda).filter(Venda.cliente_id == cliente.id).all()
            if not vendas_cliente:
                continue

            venda_ids = [v.id for v in vendas_cliente]
            itens = self.db.query(ItemVenda, Produto).join(Produto, ItemVenda.produto_id == Produto.id).filter(ItemVenda.venda_id.in_(venda_ids)).all()

            # Cálculo de Faturamento Último Mês vs Média 6 Meses
            total_6m = sum(v.valor_total for v in vendas_cliente if v.data_venda and v.data_venda >= limite_6m)
            media_6m = total_6m / 6.0

            venda_ult_mes = sum(v.valor_total for v in vendas_cliente if v.data_venda and v.data_venda >= limite_1m_inicio)
            crescimento = ((venda_ult_mes - media_6m) / media_6m * 100) if media_6m > 0 else 0.0

            # Top Fábricas do Cliente
            fabricas_map = {}
            for v in vendas_cliente:
                fabricas_map[v.fabrica_id] = fabricas_map.get(v.fabrica_id, 0.0) + (v.valor_total or 0.0)
            top_fabricas = sorted(fabricas_map.items(), key=lambda x: x[1], reverse=True)[:10]
            top_fabricas_list = [{"fabrica_id": f_id, "valor": val} for f_id, val in top_fabricas]

            # Inserção do registro de analytics do cliente
            analise = ClienteAnalytics(
                cliente_id=cliente.id,
                venda_ultimo_mes=venda_ult_mes,
                media_ultimos_6_meses=media_6m,
                crescimento_percentual=crescimento,
                top_fabricas_json=json.dumps(top_fabricas_list),
                sugestoes_fabricas_json=json.dumps([]), # Lógica cruzada pode ser aplicada aqui
                produtos_recomendados_json=json.dumps([]),
                produtos_parados_json=json.dumps([]),
                produtos_risco_inatividade_json=json.dumps([]),
                produtos_sem_segunda_compra_json=json.dumps([]),
            )
            self.db.add(analise)
        self.db.flush()

    def _processar_fabrica_analytics(self):
        """Consolida indicadores estratégicos por Fábrica e Região."""
        vendas = self.db.query(Venda, Cliente).join(Cliente, Venda.cliente_id == Cliente.id, isouter=True).all()
        
        mapa_fabrica_regiao = {}
        for venda, cliente in vendas:
            regiao = cliente.micro_regiao if cliente and cliente.micro_regiao else "DESCONHECIDA"
            chave = (venda.fabrica_id, regiao)
            if chave not in mapa_fabrica_regiao:
                mapa_fabrica_regiao[chave] = {"vendas": 0.0, "volume": 0.0}
            mapa_fabrica_regiao[chave]["vendas"] += venda.valor_total or 0.0

        for (fabrica_id, regiao), dados in mapa_fabrica_regiao.items():
            item = FabricaAnalytics(
                fabrica_id=fabrica_id,
                regiao_imediata=regiao,
                total_vendas=dados["vendas"],
                volume_vendido=dados["volume"],
                tendencia_venda="ESTAVEL",
                top_produtos_json=json.dumps([]),
            )
            self.db.add(item)
        self.db.flush()

    def _processar_alertas_comerciais(self):
        """Gera tarefas automatizadas para a Central de Alertas."""
        # Exemplo de regra: Clientes sem comprar há mais de 90 dias
        hoje = date.today()
        limite_inatividade = hoje - timedelta(days=90)

        clientes = self.db.query(Cliente).all()
        for cliente in clientes:
            ultima_venda = self.db.query(Venda).filter(Venda.cliente_id == cliente.id).order_by(Venda.data_venda.desc()).first()
            if ultima_venda and ultima_venda.data_venda and ultima_venda.data_venda < limite_inatividade:
                alerta = AlertaComercial(
                    tipo_alerta="INATIVIDADE_90_DIAS",
                    cliente_id=cliente.id,
                    vendedor_id=ultima_venda.vendedor_id,
                    fabrica_id=ultima_venda.fabrica_id,
                    descricao_acao=f"Cliente {cliente.razao_social or cliente.id} - Sem compras há mais de 90 dias.",
                    data_referencia=ultima_venda.data_venda,
                )
                self.db.add(alerta)
        self.db.flush()