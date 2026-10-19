from collections import defaultdict
from types import SimpleNamespace
from datetime import date, timedelta
from typing import Any, Dict, List, Optional
from sqlalchemy import func
from sqlalchemy.orm import Session

from src.backend.app.models.cliente import Cliente
from src.backend.app.models.item_venda import ItemVenda
from src.backend.app.models.produto import Produto
from src.backend.app.models.venda import Venda
from src.backend.app.services.regras_service import MotorRegras
from src.backend.app.services.identidade_cliente import chave_cliente, IdentidadeCliente
from src.backend.app.services.datas import hoje_comercial
from src.backend.app.services.evidencia_produtos import recompra_nao_confirmada, ultimos_pedidos_desconhecidos


class RecompraService:

    def __init__(self, db_session: Session):
        self.db = db_session

    def obter_identificador_grupo(self, cliente_id: int) -> Optional[str]:
        cliente = (
            self.db.query(Cliente.id, Cliente.grupo_economico)
            .filter(Cliente.id == cliente_id)
            .first()
        )
        if not cliente:
            return None
        return chave_cliente(cliente.id, cliente.grupo_economico)

    def obter_alertas_globais_alto_volume(
        self,
        limite_alertas: int = 10,
        data_referencia: Optional[date] = None,
        ref_date: Optional[date] = None,
    ) -> List[Dict[str, Any]]:
        """Gera os cards prioritários para o Dashboard/Home."""
        ref = ref_date or data_referencia or hoje_comercial()

        media_geral = self.db.query(func.avg(ItemVenda.quantidade)).join(Venda,Venda.id==ItemVenda.venda_id).filter(Venda.data_venda<=ref).scalar() or 10.0
        corte_volume = float(media_geral) * 1.2

        registros = (
            self.db.query(
                Cliente.id.label("cliente_id"),
                Cliente.razao_social,
                Cliente.grupo_economico,
                Cliente.cnpj_cpf,
                Produto.id.label("produto_id"),
                Produto.sku,
                Produto.fabrica_id,
                Produto.nome.label("produto_nome"),
                Venda.data_venda,
                ItemVenda.quantidade,
            )
            .join(Cliente, Cliente.id == Venda.cliente_id)
            .join(ItemVenda, ItemVenda.venda_id == Venda.id)
            .join(Produto, Produto.id == ItemVenda.produto_id)
            .order_by(Venda.data_venda.asc())
            .all()
        )

        agrupamento = defaultdict(lambda: {"datas": set(), "quantidades": [], "meta": None})

        motor = MotorRegras(self.db)
        sem_itens = ultimos_pedidos_desconhecidos(self.db,ref,motor.identidade)
        for r in registros:
            if r.data_venda > ref or motor.bloqueada(r.cliente_id,r.fabrica_id,ref):
                continue
            pid = motor.produto(r.produto_id,r.cliente_id,ref,r.data_venda)
            p = motor.produtos[pid]
            r = SimpleNamespace(**{**r._mapping,'produto_id':pid,'sku':p.sku,'produto_nome':p.nome})
            grupo_chave = (motor.identidade.id(r.cliente_id),pid)
            agrupamento[grupo_chave]["datas"].add(r.data_venda)
            agrupamento[grupo_chave]["quantidades"].append(r.quantidade)
            if not agrupamento[grupo_chave]["meta"]:
                agrupamento[grupo_chave]["meta"] = r

        alertas = []

        for (grupo_id, prod_id), dados in agrupamento.items():
            datas = sorted(dados["datas"])
            if len(datas) < 2:
                continue

            vol_medio = sum(dados["quantidades"]) / len(dados["quantidades"])
            if vol_medio < corte_volume:
                continue

            intervalos = [(datas[i] - datas[i - 1]).days for i in range(1, len(datas))]
            periodicidade = sum(intervalos) / len(intervalos)
            ultima_compra = datas[-1]
            meta = dados['meta']
            if recompra_nao_confirmada(ultima_compra,sem_itens.get((grupo_id,meta.fabrica_id))):
                continue
            dias_desde_ultima = (ref - ultima_compra).days
            dias_esperados = int(round(periodicidade))
            dias_atraso = dias_desde_ultima - dias_esperados

            if dias_atraso > 5:
                status = "Risco Crítico de Churn" if dias_atraso > (dias_esperados * 1.5) else "Atrasado"
                meta = dados["meta"]

                alertas.append({
                    "cliente_id": meta.cliente_id,
                    "razao_social": meta.razao_social,
                    "grupo_economico": meta.grupo_economico or meta.cnpj_cpf,
                    "produto_id": prod_id,
                    "sku": meta.sku,
                    "nome_produto": meta.produto_nome,
                    "volume_medio_pedido": int(round(vol_medio)),
                    "periodicidade_dias": round(periodicidade, 1),
                    "dias_atraso": dias_atraso,
                    "status": status,
                })

        alertas.sort(
            key=lambda x: (x["status"] == "Risco Crítico de Churn", x["dias_atraso"] * x["volume_medio_pedido"]),
            reverse=True,
        )

        return alertas[:limite_alertas]

    def analisar_oportunidades_cliente(
        self,
        cliente_id: int,
        data_referencia: Optional[date] = None,
        ref_date: Optional[date] = None,
        margem_tolerancia_dias: int = 5,
    ) -> List[Dict[str, Any]]:
        """Mapeia os ciclos de recompra por produto para um cliente ou grupo econômico."""
        ref = ref_date or data_referencia or hoje_comercial()
        cliente = self.db.get(Cliente, cliente_id)
        if cliente is None:
            return []
        ids_clientes = IdentidadeCliente(self.db).fiscais(cliente_id)

        registros = (
            self.db.query(
                Produto.id.label("produto_id"),
                Produto.sku,
                Produto.fabrica_id,
                Produto.nome.label("produto_nome"),
                Venda.data_venda,
                ItemVenda.quantidade,
            )
            .join(Cliente, Cliente.id == Venda.cliente_id)
            .join(ItemVenda, ItemVenda.venda_id == Venda.id)
            .join(Produto, Produto.id == ItemVenda.produto_id)
            .filter(Cliente.id.in_(ids_clientes), Venda.data_venda <= ref)
            .order_by(Venda.data_venda.asc())
            .all()
        )

        produtos_map = defaultdict(lambda: {"sku": "", "nome": "", "compras": []})
        motor = MotorRegras(self.db)
        sem_itens = ultimos_pedidos_desconhecidos(self.db,ref,motor.identidade)
        for r in registros:
            if motor.bloqueada(cliente_id,r.fabrica_id,ref):
                continue
            pid = motor.produto(r.produto_id,cliente_id,ref,r.data_venda)
            p = motor.produtos[pid]
            r = SimpleNamespace(**{**r._mapping,'produto_id':pid,'sku':p.sku,'produto_nome':p.nome})
            produtos_map[r.produto_id]["sku"] = r.sku
            produtos_map[r.produto_id]["nome"] = r.produto_nome
            produtos_map[r.produto_id]["fabrica_id"] = r.fabrica_id
            produtos_map[r.produto_id]["compras"].append((r.data_venda, r.quantidade))

        oportunidades = []

        for pid, dados in produtos_map.items():
            compras = sorted(dados["compras"], key=lambda x: x[0])
            datas_unicas = sorted({c[0] for c in compras})
            if len(datas_unicas) < 2:
                continue

            intervalos = [(datas_unicas[i] - datas_unicas[i - 1]).days for i in range(1, len(datas_unicas))]
            periodicidade = sum(intervalos) / len(intervalos)
            ultima_compra = datas_unicas[-1]
            if recompra_nao_confirmada(ultima_compra,sem_itens.get((motor.identidade.id(cliente_id),dados['fabrica_id']))):
                continue
            dias_desde_ultima = (ref - ultima_compra).days

            dias_esperados = int(round(periodicidade))
            data_prevista = ultima_compra + timedelta(days=dias_esperados)
            dias_atraso = dias_desde_ultima - dias_esperados

            if dias_atraso > (dias_esperados * 1.5):
                status, prioridade = "Risco Crítico de Churn", 1
            elif dias_atraso > margem_tolerancia_dias:
                status, prioridade = "Atrasado (Reposição Necessária)", 2
            elif abs(dias_atraso) <= margem_tolerancia_dias:
                status, prioridade = "Oportunidade (Janela Ideal de Compra)", 3
            else:
                status, prioridade = "Em Dia", 4

            media_volume = sum(c[1] for c in compras) / len(compras)

            oportunidades.append({
                "produto_id": pid,
                "sku": dados["sku"],
                "nome": dados["nome"],
                "total_compras_historico": len(datas_unicas),
                "dias_desde_ultima_compra": dias_desde_ultima,
                "periodicidade_media_dias": round(periodicidade, 1),
                "previsao_proxima_compra": data_prevista.strftime("%d/%m/%Y"),
                "dias_atraso": max(0, dias_atraso),
                "volume_medio_pedido": int(round(media_volume)),
                "status": status,
                "prioridade": prioridade,
            })

        oportunidades.sort(key=lambda x: (x["prioridade"], -x["dias_atraso"]))
        return oportunidades
