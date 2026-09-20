from collections import defaultdict
from datetime import date
import re
from typing import Any, Dict, List, Optional
from dateutil.relativedelta import relativedelta
from sqlalchemy import or_
from sqlalchemy.orm import Session

from src.backend.app.core.security import gerar_blind_index
from src.backend.app.models.cliente import Cliente
from src.backend.app.models.fabrica import Fabrica
from src.backend.app.models.item_venda import ItemVenda
from src.backend.app.models.produto import Produto
from src.backend.app.models.venda import Venda
from src.backend.app.services.colaborativo_service import ColaborativoService


class ClienteService:

    def __init__(self, db_session: Session):
        self.db = db_session
        self.colaborativo = ColaborativoService(db_session=db_session)

    def buscar_por_termo(self, termo: str, limite: int = 15) -> List[Dict[str, Any]]:
        """Busca híbrida: Blind Index para documento ou varredura decifrada para texto."""
        termo_limpo = termo.strip()
        apenas_digitos = re.sub(r"\D", "", termo_limpo)

        # 1. Busca Exata por CNPJ/CPF via Blind Index O(1)
        if len(apenas_digitos) >= 8:
            hash_busca = gerar_blind_index(apenas_digitos)
            cliente = (
                self.db.query(Cliente)
                .filter(Cliente.cnpj_hash == hash_busca)
                .first()
            )
            if cliente:
                return [
                    {
                        "id": cliente.id,
                        "razao_social": cliente.razao_social,
                        "nome_fantasia": cliente.nome_fantasia,
                        "cnpj_cpf": cliente.cnpj_cpf,
                        "grupo_economico": cliente.grupo_economico,
                        "cidade": cliente.cidade,
                        "estado": cliente.estado,
                    }
                ]

        # 2. Busca por Grupo Econômico ou Localidade (Indexados no banco)
        clientes_query = (
            self.db.query(Cliente)
            .filter(
                or_(
                    Cliente.grupo_economico.ilike(f"%{termo_limpo}%"),
                    Cliente.cidade.ilike(f"%{termo_limpo}%"),
                )
            )
            .limit(limite)
            .all()
        )
        if clientes_query:
            return [
                {
                    "id": c.id,
                    "razao_social": c.razao_social,
                    "nome_fantasia": c.nome_fantasia,
                    "cnpj_cpf": c.cnpj_cpf,
                    "grupo_economico": c.grupo_economico,
                    "cidade": c.cidade,
                    "estado": c.estado,
                }
                for c in clientes_query
            ]

        # 3. Varredura decifrada em memória (Fallback para Razão Social / Nome Fantasia)
        candidatos = self.db.query(Cliente).limit(300).all()
        termo_lower = termo_limpo.lower()
        resultados = []

        for c in candidatos:
            razao = (c.razao_social or "").lower()
            fantasia = (c.nome_fantasia or "").lower()
            if termo_lower in razao or termo_lower in fantasia:
                resultados.append(
                    {
                        "id": c.id,
                        "razao_social": c.razao_social,
                        "nome_fantasia": c.nome_fantasia,
                        "cnpj_cpf": c.cnpj_cpf,
                        "grupo_economico": c.grupo_economico,
                        "cidade": c.cidade,
                        "estado": c.estado,
                    }
                )
                if len(resultados) >= limite:
                    break

        return resultados

    def obter_dossie_cliente(
        self, cliente_id: int, ref_date: Optional[date] = None
    ) -> Optional[Dict[str, Any]]:
        """Dossiê analítico 360: histórico, ciclo de fábrica, reposição, abandono e YoY."""
        ref = ref_date or date.today()

        cliente = self.db.query(Cliente).filter(Cliente.id == cliente_id).first()
        if not cliente:
            return None

        registros = (
            self.db.query(
                Venda.id.label("venda_id"),
                Venda.data_venda,
                Venda.valor_total,
                Fabrica.id.label("fabrica_id"),
                Fabrica.nome_fantasia.label("fabrica_nome"),
                ItemVenda.produto_id,
                ItemVenda.quantidade,
                Produto.sku,
                Produto.nome.label("produto_nome"),
            )
            .join(ItemVenda, ItemVenda.venda_id == Venda.id)
            .join(Produto, Produto.id == ItemVenda.produto_id)
            .join(Fabrica, Fabrica.id == Venda.fabrica_id)
            .filter(Venda.cliente_id == cliente_id)
            .order_by(Venda.data_venda.asc())
            .all()
        )

        base_info = {
            "cliente_id": cliente.id,
            "razao_social": cliente.razao_social,
            "cnpj_cpf": cliente.cnpj_cpf,
            "micro_regiao": cliente.micro_regiao,
            "grupo_economico": cliente.grupo_economico,
        }

        if not registros:
            return {
                **base_info,
                "mensagem": "Cliente sem registros de vendas para análise.",
                "resumo_fabricas": [],
                "sugestoes_reposicao": [],
                "produtos_em_abandono": [],
                "performance_yoy": None,
                "sugestoes_expansao_mix": [],
            }

        return {
            **base_info,
            "resumo_fabricas": self._analisar_fabricas(registros, ref),
            "sugestoes_reposicao": self._analisar_reposicao(registros, ref),
            "produtos_em_abandono": self._analisar_produtos_abandono(registros, ref),
            "performance_yoy": self._analisar_yoy(registros, ref),
            "sugestoes_expansao_mix": (
                self.colaborativo.recomendar_produtos_cliente(cliente_id, top_n_produtos=4)
                if hasattr(self.colaborativo, "recomendar_produtos_cliente")
                else []
            ),
        }

    def _analisar_fabricas(self, registros: list, ref: date) -> List[Dict[str, Any]]:
        fabricas_map = defaultdict(lambda: {"nome": "", "pedidos": {}})
        for r in registros:
            fabricas_map[r.fabrica_id]["nome"] = r.fabrica_nome
            fabricas_map[r.fabrica_id]["pedidos"][r.venda_id] = r.data_venda

        status_fabricas = []
        for fid, dados in fabricas_map.items():
            datas = sorted(dados["pedidos"].values())
            ultima_compra = datas[-1]
            dias_sem_comprar = (ref - ultima_compra).days

            if len(datas) > 1:
                intervalos = [(datas[i] - datas[i - 1]).days for i in range(1, len(datas))]
                ciclo_medio = int(sum(intervalos) / len(intervalos))
            else:
                ciclo_medio = 90

            limite_90d = ultima_compra + relativedelta(days=90)
            dias_para_vencer = ciclo_medio - dias_sem_comprar

            if dias_sem_comprar >= 90:
                status = "Inativo na Fábrica"
                gatilho = "ATRASADO"
            elif dias_sem_comprar >= ciclo_medio:
                status = "Ciclo Atrasado"
                gatilho = "ATRASADO"
            elif dias_sem_comprar + 7 >= ciclo_medio:
                status = "Janela de Recompra (7 dias)"
                gatilho = "PREVISAO_7_DIAS"
            else:
                status = "Ativo"
                gatilho = "REGULAR"

            status_fabricas.append(
                {
                    "fabrica_id": fid,
                    "fabrica": dados["nome"],
                    "ultima_compra": ultima_compra.strftime("%d/%m/%Y"),
                    "dias_sem_comprar": dias_sem_comprar,
                    "ciclo_medio_dias": ciclo_medio,
                    "dias_para_vencer": dias_para_vencer,
                    "data_limite_inatividade": limite_90d.strftime("%d/%m/%Y"),
                    "status": status,
                    "status_gatilho": gatilho,
                    "risco_bloqueio_neste_mes": (
                        limite_90d.month == ref.month and limite_90d.year == ref.year
                    ),
                }
            )

        status_fabricas.sort(key=lambda x: x["dias_para_vencer"])
        return status_fabricas

    def _analisar_reposicao(self, registros: list, ref: date) -> List[Dict[str, Any]]:
        produtos_map = defaultdict(lambda: {"sku": "", "nome": "", "compras": []})
        for r in registros:
            produtos_map[r.produto_id]["sku"] = r.sku
            produtos_map[r.produto_id]["nome"] = r.produto_nome
            produtos_map[r.produto_id]["compras"].append((r.data_venda, r.quantidade))

        sugestoes = []
        for pid, dados in produtos_map.items():
            compras = sorted(dados["compras"], key=lambda x: x[0])
            datas = [c[0] for c in compras]
            if len(datas) < 2:
                continue

            intervalos = [(datas[i] - datas[i - 1]).days for i in range(1, len(datas))]
            ciclo = int(sum(intervalos) / len(intervalos))
            ultima = datas[-1]
            dias_desde_ultima = (ref - ultima).days
            atraso = dias_desde_ultima - ciclo

            if atraso >= -5 and dias_desde_ultima < (ciclo * 2):
                media_qtd = sum(c[1] for c in compras) / len(compras)
                sugestoes.append(
                    {
                        "produto_id": pid,
                        "sku": dados["sku"],
                        "nome": dados["nome"],
                        "ciclo_medio": ciclo,
                        "dias_desde_ultima": dias_desde_ultima,
                        "status": "Reposição Atrasada" if atraso > 0 else "Janela Ideal",
                        "volume_habitual": round(float(media_qtd), 0),
                    }
                )

        return sugestoes

    def _analisar_produtos_abandono(self, registros: list, ref: date) -> List[Dict[str, Any]]:
        produtos_map = defaultdict(lambda: {"sku": "", "nome": "", "datas": []})
        for r in registros:
            produtos_map[r.produto_id]["sku"] = r.sku
            produtos_map[r.produto_id]["nome"] = r.produto_nome
            produtos_map[r.produto_id]["datas"].append(r.data_venda)

        abandonados = []
        for pid, dados in produtos_map.items():
            datas = sorted(dados["datas"])
            if len(datas) < 3:
                continue

            intervalos = [(datas[i] - datas[i - 1]).days for i in range(1, len(datas))]
            ciclo = int(sum(intervalos) / len(intervalos))
            dias_sem_comprar = (ref - datas[-1]).days

            if dias_sem_comprar > (ciclo * 2.5) and dias_sem_comprar >= 60:
                abandonados.append(
                    {
                        "produto_id": pid,
                        "sku": dados["sku"],
                        "nome": dados["nome"],
                        "dias_parado": dias_sem_comprar,
                        "ciclo_habitual": ciclo,
                        "total_vezes_comprado": len(datas),
                    }
                )

        return abandonados

    def _analisar_yoy(self, registros: list, ref: date) -> Dict[str, Any]:
        mes_recente_inicio = (ref.replace(day=1) - relativedelta(days=1)).replace(day=1)
        ano_anterior_inicio = mes_recente_inicio - relativedelta(years=1)

        vendas_unicas = {}
        for r in registros:
            vendas_unicas[r.venda_id] = (r.data_venda, r.valor_total)

        fat_recente = sum(
            valor
            for data_v, valor in vendas_unicas.values()
            if data_v.year == mes_recente_inicio.year and data_v.month == mes_recente_inicio.month
        )

        fat_anterior = sum(
            valor
            for data_v, valor in vendas_unicas.values()
            if data_v.year == ano_anterior_inicio.year and data_v.month == ano_anterior_inicio.month
        )

        variacao = (
            ((fat_recente - fat_anterior) / fat_anterior * 100)
            if fat_anterior > 0
            else 0.0
        )

        return {
            "periodo_recente": mes_recente_inicio.strftime("%m/%Y"),
            "periodo_comparado": ano_anterior_inicio.strftime("%m/%Y"),
            "faturamento_recente": round(float(fat_recente), 2),
            "faturamento_ano_anterior": round(float(fat_anterior), 2),
            "crescimento_pct": round(float(variacao), 2),
        }