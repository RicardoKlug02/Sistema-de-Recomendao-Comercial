import json
import sys
from pathlib import Path

raiz = Path(__file__).resolve().parent.parent
if str(raiz) not in sys.path:
    sys.path.insert(0, str(raiz))

from sqlalchemy import func
from sqlalchemy.orm import Session
from src.backend.app.core.database import engine
from src.backend.app.core.security import decrypt_data
from src.backend.app.models.cliente import Cliente
from src.backend.app.models.venda import Venda
from src.backend.app.services.resumo_cliente import ClienteDossieService


def testar_dossie_cliente_real():
    with Session(engine) as session:
        # Busca o cliente com maior volume de pedidos usando func.count()
        top_cliente = (
            session.query(Venda.cliente_id, func.count(Venda.id).label("total_vendas"))
            .group_by(Venda.cliente_id)
            .order_by(func.count(Venda.id).desc())
            .first()
        )

        if not top_cliente:
            print("Nenhuma venda encontrada na base de dados para teste.")
            return

        cliente_id_alvo = top_cliente[0]
        cliente_obj = session.query(Cliente).filter(Cliente.id == cliente_id_alvo).first()
        nome_cliente = (
            decrypt_data(cliente_obj.razao_social)
            if cliente_obj and cliente_obj.razao_social
            else "N/D"
        )

        print("=" * 85)
        print(f"GERANDO DOSSIÊ DO CLIENTE: {nome_cliente} (ID: {cliente_id_alvo})")
        print(f"Total de vendas registradas no histórico: {top_cliente[1]}")
        print("=" * 85)

        service = ClienteDossieService(db_session=session)
        dossie = service.gerar_dossie_completo(cliente_id=cliente_id_alvo)

        print(json.dumps(dossie, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    testar_dossie_cliente_real()