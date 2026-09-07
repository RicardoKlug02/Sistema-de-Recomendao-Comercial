from pathlib import Path
import sys

raiz = Path(__file__).resolve().parent.parent
if str(raiz) not in sys.path:
    sys.path.insert(0, str(raiz))

from sqlalchemy.orm import Session
from src.backend.app.core.database import engine
from src.backend.app.core.security import decrypt_data
from src.backend.app.models.cliente import Cliente
from src.backend.app.services.colaborativo_service import ColaborativoService

with Session(engine) as session:
    service = ColaborativoService(db_session=session)

    # Pega o primeiro cliente com compras
    cliente = session.query(Cliente).first()

    if not cliente:
        print("Nenhum cliente cadastrado.")
    else:
        nome_cliente = decrypt_data(cliente.razao_social)
        print(f"Analisando perfil do cliente ID {cliente.id} ({nome_cliente})...\n")

        # 1. Clientes com perfil parecido
        vizinhos = service.encontrar_clientes_similares(cliente.id, top_k=3)
        print("--- Clientes com perfil de compra similar ---")
        for v in vizinhos:
            vizinho_obj = (
                session.query(Cliente).filter(Cliente.id == v["cliente_id"]).first()
            )
            nome_vizinho = (
                decrypt_data(vizinho_obj.razao_social)
                if vizinho_obj
                else "Desconhecido"
            )
            print(
                f"• Cliente {v['cliente_id']} ({nome_vizinho}) - Similaridade: {v['similaridade']}%"
            )

        # 2. Produtos recomendados para expandir a carteira
        recomendacoes = service.recomendar_produtos_cliente(cliente.id, top_n_produtos=5)
        print("\n--- Produtos recomendados para oferta (Expansão de Mix) ---")
        if not recomendacoes:
            print("Nenhuma oportunidade encontrada ou dados insuficientes.")
        else:
            for rec in recomendacoes:
                print(f"★ [{rec['sku']}] {rec['nome']}")
                print(f"   Score: {rec['score_relevancia']} | {rec['motivo']}")
                print("-" * 60)