import sys
from pathlib import Path

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
    
    cliente = session.query(Cliente).filter(Cliente.id == 20).first()

    if not cliente:
        print("Nenhum cliente cadastrado.")
    else:
        nome_cliente = decrypt_data(cliente.razao_social)
        print(
            f"Analisando perfil do cliente ID {cliente.id} ({nome_cliente})...\n"
        )

        # 1. Grupos/Redes com perfil parecido (método atualizado)
        vizinhos = service.encontrar_grupos_similares(cliente.id, top_k=3)
        print("--- Redes/Grupos com perfil de compra similar ---")
        if not vizinhos:
            print("Nenhum grupo similar encontrado com dados suficientes.")
        else:
            for v in vizinhos:
                print(
                    f"• Grupo: {v['grupo_economico']} - Similaridade: {v['similaridade']}%"
                )

       # 2. Recomendações
        print("\n--- Produtos recomendados para oferta (Expansão de Mix) ---")
        recomendacoes = service.recomendar_produtos_cliente(
            cliente.id, top_n_produtos=5
        )
        if not recomendacoes:
            print("Nenhuma recomendação gerada para este perfil.")
        else:
            for rec in recomendacoes:
                print(f"★ [{rec['sku']}] {rec['nome']}")
                print(
                    f"   Afinidade: {rec['afinidade_percentual']}% ({rec['classificacao']})"
                )
                print(
                    f"   Sugestão de Compra: {rec['volume_sugerido_unidades']} un."
                )
                print(f"   Motivo: {rec['motivo']}")
                print("-" * 60)