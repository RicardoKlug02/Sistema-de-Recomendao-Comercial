from pathlib import Path
import sys

raiz = Path(__file__).resolve().parent.parent
if str(raiz) not in sys.path:
    sys.path.insert(0, str(raiz))

from sqlalchemy.orm import Session
from src.backend.app.core.database import engine
from src.backend.app.models.cliente import Cliente
from src.backend.app.services.recompra_service import RecompraService

with Session(engine) as session:
    primeiro_cliente = session.query(Cliente).first()

    if not primeiro_cliente:
        print("Nenhum cliente cadastrado no banco.")
    else:
        service = RecompraService(db_session=session)

        print(
            f"Analisando reposições para o cliente ID: {primeiro_cliente.id} ({primeiro_cliente.cnpj_cpf})...\n"
        )
        alertas = service.analisar_oportunidades_cliente(
            cliente_id=primeiro_cliente.id
        )

        if not alertas:
            print("Nenhum produto precisando de reposição no momento.")
        else:
            for item in alertas:
                print(
                    f"[{item['urgencia']}] Produto: {item['produto']} (SKU: {item['sku']})"
                )
                print(
                    f"   Ciclo médio: {item['ciclo_medio_dias']} dias | Dias sem comprar: {item['dias_desde_ultima_compra']} dias | Atraso: {item.get('dias_atraso')} dias"
                )
                print("-" * 60)