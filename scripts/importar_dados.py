import sys
from pathlib import Path

# Ajusta sys.path para reconhecer a pasta src
raiz = Path(__file__).resolve().parent.parent
if str(raiz) not in sys.path:
    sys.path.insert(0, str(raiz))

from sqlalchemy.orm import Session
from src.backend.app.core.database import Base, engine
from src.backend.app.services.excel_service import ExcelService

if __name__ == "__main__":
    # Garante que as tabelas existam no Postgres
    Base.metadata.create_all(bind=engine)

    # 1. Defina aqui os caminhos para as suas planilhas:
    ARQUIVO_CABECALHO = "data/raw/Pedidos Jan 26.xls"
    ARQUIVO_ITENS = "data/raw/Produtos vendidos Jan 26.xls"

    print("Iniciando processo de importação e anonimização...")

    with Session(engine) as session:
        service = ExcelService(db_session=session)
        resultado = service.importar_processo_completo(
            path_cab=ARQUIVO_CABECALHO,
            path_itens=ARQUIVO_ITENS
        )
        print("Resultado:", resultado)