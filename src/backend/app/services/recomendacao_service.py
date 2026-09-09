from datetime import date
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from src.backend.app.core.security import decrypt_data
from src.backend.app.models.cliente import Cliente
from src.backend.app.models.item_venda import ItemVenda
from src.backend.app.models.produto import Produto
from src.backend.app.models.venda import Venda
from src.backend.app.services.associacao_service import AssociacaoService
from src.backend.app.services.colaborativo_service import ColaborativoService
from src.backend.app.services.recompra_service import RecompraService


class RecomendacaoService:

    def __init__(self, db_session: Session):
        self.db = db_session
        self.colaborativo = ColaborativoService(db_session=db_session)
        self.recompra = RecompraService(db_session=db_session)
        self.associacao = AssociacaoService(db_session=db_session)

    def obter_painel_visao_360(
        self,
        cliente_id: int,
        data_referencia: Optional[date] = None,
    ) -> Dict[str, Any]:
        """Entrega o dossiê consolidado do cliente com decriptação de dados pessoais."""
        cliente = (
            self.db.query(Cliente).filter(Cliente.id == cliente_id).first()
        )
        if not cliente:
            return {}

        # 1. Alertas de Recompra & Churn
        alertas_recompra = self.recompra.analisar_oportunidades_cliente(
            cliente_id=cliente.id,
            data_referencia=data_referencia,
        )

        # 2. Expansão de Mix via Filtragem Colaborativa
        sugestoes_mix = self.colaborativo.recomendar_produtos_cliente(
            cliente_id=cliente.id,
            top_k_vizinhos=5,
            top_n_produtos=5,
        )

        # 3. Histórico dos últimos pedidos
        ultimas_vendas = (
            self.db.query(Venda)
            .filter(Venda.cliente_id == cliente.id)
            .order_by(Venda.data_venda.desc())
            .limit(5)
            .all()
        )
        historico_vendas = [
            {
                "pedido": v.numero_pedido,
                "data": v.data_venda,
                "total": v.valor_total,
            }
            for v in ultimas_vendas
        ]

        return {
            "cliente_id": cliente.id,
            "razao_social": decrypt_data(cliente.razao_social)
            if cliente.razao_social
            else "",
            "codigo_analitico": cliente.cnpj_cpf,
            "grupo_economico": cliente.grupo_economico,
            "alertas_recompra": alertas_recompra,
            "expansao_mix": sugestoes_mix,
            "ultimos_pedidos": historico_vendas,
        }

    def obter_cross_selling_orcamento(
        self, itens_ids: List[int]
    ) -> List[Dict[str, Any]]:
        """Sugere produtos para cross-selling enquanto o vendedor digita um orçamento."""
        return self.associacao.recomendar_cross_selling(produto_ids=itens_ids)

    def obter_alertas_home(self, limite: int = 10) -> List[Dict[str, Any]]:
        """Varre a carteira para a tela inicial."""
        alertas = self.recompra.obter_alertas_globais_alto_volume(
            limite_alertas=limite
        )
        # Descriptografa os nomes para exibição direta
        for a in alertas:
            if "razao_social_raw" in a:
                a["razao_social"] = decrypt_data(a.pop("razao_social_raw"))
        return alertas