import math
from collections import defaultdict
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from src.backend.app.models.fabrica import Fabrica
from src.backend.app.services.regras_service import MotorRegras
from src.backend.app.services.identidade_cliente import chave_cliente
from src.backend.app.services.datas import hoje_comercial

from src.backend.app.models.cliente import Cliente
from src.backend.app.models.item_venda import ItemVenda
from src.backend.app.models.produto import Produto
from src.backend.app.models.venda import Venda


class ColaborativoService:

    def __init__(self, db_session: Session):
        self.db = db_session

    def _obter_identificador_grupo(self, cliente_id: int) -> Optional[str]:
        cliente = (
            self.db.query(Cliente.grupo_economico, Cliente.id)
            .filter(Cliente.id == cliente_id)
            .first()
        )
        if not cliente:
            return None
        return chave_cliente(cliente.id, cliente.grupo_economico)

    def _carregar_perfis_consumo(self, ref_date=None, motor=None, cliente_alvo=None) -> Dict[str, Dict[int, float]]:
        """Mapeia o consumo agregado por grupo econômico: {grupo: {produto_id: quantidade_total}}."""
        registros = (
            self.db.query(
                Cliente.grupo_economico,
                Cliente.id,
                ItemVenda.produto_id,
                Venda.data_venda,
                func.sum(ItemVenda.quantidade).label("quantidade"),
            )
            .join(Venda, Venda.cliente_id == Cliente.id)
            .join(ItemVenda, ItemVenda.venda_id == Venda.id)
            .filter(Venda.data_venda <= (ref_date or hoje_comercial()))
            .group_by(Cliente.id, Cliente.grupo_economico, ItemVenda.produto_id, Venda.data_venda)
            .all()
        )

        perfis: Dict[str, Dict[int, float]] = defaultdict(lambda: defaultdict(float))
        for r in registros:
            chave_grupo = chave_cliente(r.id, r.grupo_economico)
            pid = r.produto_id
            if motor is not None:
                if motor.bloqueada(cliente_alvo,motor.produtos[pid].fabrica_id,ref_date):
                    continue
                pid = motor.produto(pid,cliente_alvo,ref_date,r.data_venda)
            perfis[chave_grupo][pid] += float(r.quantidade)

        return perfis

    @staticmethod
    def _calcular_similaridade_cosseno(vetor_a: Dict[int, float], vetor_b: Dict[int, float]) -> float:
        intersecao = set(vetor_a.keys()) & set(vetor_b.keys())
        if not intersecao:
            return 0.0

        produto_escalar = sum(vetor_a[p] * vetor_b[p] for p in intersecao)
        norma_a = math.sqrt(sum(v ** 2 for v in vetor_a.values()))
        norma_b = math.sqrt(sum(v ** 2 for v in vetor_b.values()))

        if norma_a == 0 or norma_b == 0:
            return 0.0

        return produto_escalar / (norma_a * norma_b)

    def encontrar_grupos_similares(self, cliente_id: int, top_k: int = 5, ref_date=None) -> List[Dict[str, Any]]:
        grupo_alvo = self._obter_identificador_grupo(cliente_id)
        if not grupo_alvo:
            return []

        motor = MotorRegras(self.db)
        perfis = self._carregar_perfis_consumo(ref_date,motor,cliente_id)
        if grupo_alvo not in perfis:
            return []

        perfil_alvo = perfis[grupo_alvo]
        scores = []
        nomes = {chave_cliente(c.id,c.grupo_economico): (c.grupo_economico or c.razao_social).strip()
                 for c in motor.identidade.clientes.values()}

        for outro_grupo, outro_perfil in perfis.items():
            if outro_grupo == grupo_alvo:
                continue
            sim = self._calcular_similaridade_cosseno(perfil_alvo, outro_perfil)
            if sim > 0:
                scores.append({
                    "grupo_economico": nomes[outro_grupo],
                    "similaridade": round(sim * 100, 2),
                })

        scores.sort(key=lambda x: x["similaridade"], reverse=True)
        return scores[:top_k]

    def recomendar_produtos_cliente(
        self,
        cliente_id: int,
        top_k_vizinhos: int = 5,
        top_n_produtos: int = 4,
        fabrica_id: Optional[int] = None,
        ref_date=None,
    ) -> List[Dict[str, Any]]:
        """Gera recomendações de mix cruzando com grupos econômicos de comportamento análogo."""
        grupo_alvo = self._obter_identificador_grupo(cliente_id)
        if not grupo_alvo:
            return []

        motor = MotorRegras(self.db)
        perfis = self._carregar_perfis_consumo(ref_date,motor,cliente_id)
        if grupo_alvo not in perfis or len(perfis) < 2:
            return []

        perfil_alvo = perfis[grupo_alvo]
        produtos_ja_comprados = set(perfil_alvo.keys())
        # Mesmo sem reescrever compras antigas, não sugerir o sucessor de um equivalente comprado.
        produtos_ja_comprados |= {motor.produto(pid,cliente_id,ref_date) for pid in perfil_alvo}

        vizinhos_scores = []
        for outro_grupo, outro_perfil in perfis.items():
            if outro_grupo == grupo_alvo:
                continue
            sim = self._calcular_similaridade_cosseno(perfil_alvo, outro_perfil)
            if sim > 0:
                vizinhos_scores.append((outro_grupo, sim))

        vizinhos_scores.sort(key=lambda x: x[1], reverse=True)
        vizinhos_top = vizinhos_scores[:top_k_vizinhos]

        if not vizinhos_top:
            return []

        soma_pesos = sum(sim for _, sim in vizinhos_top)
        candidatos: Dict[int, Dict[str, float]] = defaultdict(lambda: {"peso_compradores": 0.0, "volume_ponderado": 0.0})

        for outro_grupo, sim in vizinhos_top:
            perfil_vizinho = motor.perfil(perfis[outro_grupo],cliente_id,ref_date)
            for prod_id, qtd in perfil_vizinho.items():
                if prod_id in produtos_ja_comprados:
                    continue
                candidatos[prod_id]["peso_compradores"] += sim
                candidatos[prod_id]["volume_ponderado"] += (qtd * sim)

        if not candidatos:
            return []

        if fabrica_id is not None:
            permitidos = {p.id for p in self.db.query(Produto.id).filter(Produto.fabrica_id == fabrica_id)}
            candidatos = {pid: m for pid, m in candidatos.items() if pid in permitidos}
        produtos_avaliados = []
        for prod_id, metricas in candidatos.items():
            afinidade_pct = (metricas["peso_compradores"] / soma_pesos) * 100
            volume_sugerido = metricas["volume_ponderado"] / metricas["peso_compradores"]

            produtos_avaliados.append({
                "produto_id": prod_id,
                "afinidade_pct": round(afinidade_pct, 1),
                "volume_sugerido": int(math.ceil(volume_sugerido)),
            })

        produtos_avaliados.sort(key=lambda x: (x["afinidade_pct"], x["volume_sugerido"]), reverse=True)
        top_produtos = produtos_avaliados[:top_n_produtos]

        ids = [p["produto_id"] for p in top_produtos]
        produtos_db = {p.id: (p, f) for p, f in self.db.query(Produto, Fabrica).join(Fabrica, Fabrica.id == Produto.fabrica_id).filter(Produto.id.in_(ids)).all()}

        recomendacoes = []
        for item in top_produtos:
            par = produtos_db.get(item["produto_id"])
            if not par:
                continue
            prod, fabrica = par

            nota = item["afinidade_pct"]
            if nota >= 75:
                status = "Altíssima Aderência"
            elif nota >= 40:
                status = "Aderência Moderada"
            else:
                status = "Oportunidade Complementar"

            recomendacoes.append({
                "produto_id": prod.id,
                "sku": prod.sku,
                "fabrica_id": fabrica.id, "fabrica": fabrica.nome_fantasia,
                "nome": prod.nome,
                "afinidade_percentual": item["afinidade_pct"],
                "classificacao": status,
                "volume_sugerido_unidades": item["volume_sugerido"],
                "motivo": f"Comprado por redes com {item['afinidade_pct']}% de afinidade",
            })

        return recomendacoes
