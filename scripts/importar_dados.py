import sys
from pathlib import Path

raiz = Path(__file__).resolve().parent.parent
if str(raiz) not in sys.path:
    sys.path.insert(0, str(raiz))

from sqlalchemy.orm import Session
from src.backend.app.core.database import engine
from src.backend.app.services.excel_service import ExcelService

if __name__ == "__main__":
    pasta_raw = Path("data/raw")
    
    # Encontra todos os arquivos de cabeçalho
    arquivos_pedidos = sorted(pasta_raw.glob("Pedidos *.xls*"))

    with Session(engine) as session:
        service = ExcelService(db_session=session)

        for path_cab in arquivos_pedidos:
            # Extrai o sufixo (ex: "Jan 26")
            sufixo = path_cab.name.replace("Pedidos ", "")
            
            # Procura o arquivo de itens correspondente
            candidatos_itens = list(pasta_raw.glob(f"Produtos vendidos {sufixo}"))
            
            if not candidatos_itens:
                print(f"[PULADO] Nenhum arquivo de itens correspondente para: {path_cab.name}")
                continue
                
            path_itens = candidatos_itens[0]
            print(f"\nImportando: {path_cab.name} com {path_itens.name}...")
            
            resultado = service.importar_processo_completo(
                path_cab=str(path_cab), 
                path_itens=str(path_itens)
            )
            print(f"Resultado: {resultado}")