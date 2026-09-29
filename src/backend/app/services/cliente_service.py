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
        # A cifra é decifrada em lotes; não existe corte arbitrário da carteira.
        import unicodedata
        def normalizar(s):
            return "".join(c for c in unicodedata.normalize("NFKD", s or "")
                           if not unicodedata.combining(c)).casefold()
        alvo = normalizar(termo.strip())
        if not alvo:
            return []
        digitos = re.sub(r"\D", "", termo)
        hash_alvo = gerar_blind_index(digitos) if len(digitos) in (11, 14) else None
        resultados = []
        for c in self.db.query(Cliente).order_by(Cliente.id).yield_per(200):
            if (hash_alvo and c.cnpj_hash == hash_alvo) or any(alvo in normalizar(v) for v in
                (c.razao_social, c.nome_fantasia, c.grupo_economico, c.cidade)):
                resultados.append({"id": c.id, "razao_social": c.razao_social,
                    "nome_fantasia": c.nome_fantasia, "cnpj_cpf": c.cnpj_cpf,
                    "grupo_economico": c.grupo_economico, "cidade": c.cidade, "estado": c.estado})
                if len(resultados) >= limite:
                    break
        return resultados


    def obter_dossie_cliente(
        self, cliente_id: int, ref_date: Optional[date] = None, agrupar_rede: bool = False
    ) -> Optional[Dict[str, Any]]:
        """Dossiê analítico 360: histórico, ciclo de fábrica, reposição, abandono e YoY."""
        ref = ref_date or date.today()

        cliente = self.db.query(Cliente).filter(Cliente.id == cliente_id).first()
        if not cliente:
            return None

        cliente_ids = [cliente.id]
        if agrupar_rede and cliente.grupo_economico:
            cliente_ids = [c.id for c in self.db.query(Cliente.id).filter(Cliente.grupo_economico == cliente.grupo_economico)]

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
            .outerjoin(ItemVenda, ItemVenda.venda_id == Venda.id)
            .outerjoin(Produto, Produto.id == ItemVenda.produto_id)
            .join(Fabrica, Fabrica.id == Venda.fabrica_id)
            .filter(Venda.cliente_id.in_(cliente_ids), Venda.data_venda <= ref)
            .order_by(Venda.data_venda.asc())
            .all()
        )

        base_info = {
            "cliente_id": cliente.id,
            "razao_social": cliente.razao_social,
            "cnpj_cpf": cliente.cnpj_cpf,
            "micro_regiao": cliente.micro_regiao,
            "grupo_economico": cliente.grupo_economico,
            "clientes_agrupados": len(cliente_ids),
            "valor_comprado": round(sum({r.venda_id: r.valor_total for r in registros}.values()), 2),
            "pedidos_emitidos": len({r.venda_id for r in registros}),
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

        recomendacoes = self.colaborativo.recomendar_produtos_cliente(cliente_id, top_n_produtos=10)
        compradas = {r.fabrica_id for r in registros}
        sugestoes_fabricas = {}
        for sugestao in recomendacoes:
            produto = self.db.get(Produto, sugestao["produto_id"])
            if produto and produto.fabrica_id not in compradas:
                fabrica = self.db.get(Fabrica, produto.fabrica_id)
                sugestoes_fabricas[fabrica.id] = {"id": fabrica.id, "nome": fabrica.nome_fantasia,
                    "motivo": "Produtos desta fábrica são comprados por redes de consumo semelhante."}
        return {
            **base_info,
            "sugestoes_fabricas": list(sugestoes_fabricas.values()),
            "resumo_fabricas": self._analisar_fabricas(registros, ref),
            "sugestoes_reposicao": self._analisar_reposicao(registros, ref),
            "produtos_em_abandono": self._analisar_produtos_abandono(registros, ref),
            "performance_yoy": self._analisar_yoy(registros, ref),
            "sugestoes_expansao_mix": (
                recomendacoes[:4]
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
            datas = sorted(set(dados["pedidos"].values()))
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
            if r.produto_id is None:
                continue
            produtos_map[r.produto_id]["sku"] = r.sku
            produtos_map[r.produto_id]["nome"] = r.produto_nome
            produtos_map[r.produto_id]["compras"].append((r.data_venda, r.quantidade))

        sugestoes = []
        for pid, dados in produtos_map.items():
            por_data = defaultdict(int)
            for data_compra, quantidade in dados["compras"]:
                por_data[data_compra] += quantidade
            compras = sorted(por_data.items())
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
            if r.produto_id is None:
                continue
            produtos_map[r.produto_id]["sku"] = r.sku
            produtos_map[r.produto_id]["nome"] = r.produto_nome
            produtos_map[r.produto_id]["datas"].append(r.data_venda)

        abandonados = []
        for pid, dados in produtos_map.items():
            datas = sorted(set(dados["datas"]))
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
