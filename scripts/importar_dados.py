"""Importa pares do ERP; cada par é uma transação e falhas retornam exit code 1."""

import argparse
from pathlib import Path
import sys

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
from src.backend.app.core.database import SessionLocal
from src.backend.app.models.importacao import Importacao
from src.backend.app.services.excel_service import ExcelService


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pasta", type=Path, default=RAIZ / "data/raw")
    parser.add_argument(
        "--permitir-atualizacao",
        action="store_true",
        help="Permitir alterações em pedidos já existentes após conferência.",
    )
    args = parser.parse_args()
    arquivos = sorted(args.pasta.glob("Pedidos *.xls*"))
    if not arquivos:
        print("Nenhuma planilha de pedidos encontrada.")
        return 1
    falhas = 0
    with SessionLocal() as db:
        for cab in arquivos:
            itens = cab.with_name(cab.name.replace("Pedidos ", "Produtos vendidos ", 1))
            if not itens.is_file():
                print(f"{cab.name}: falta a planilha de itens correspondente.")
                falhas += 1
                continue
            resultado = ExcelService(db).importar_processo_completo(
                cab, itens, permitir_atualizacao=args.permitir_atualizacao, commit=False
            )
            db.add(
                Importacao(
                    arquivos=f"{cab.name} + {itens.name}",
                    usuario="CLI",
                    status=resultado["status"],
                    mensagem=resultado["mensagem"],
                )
            )
            db.commit()
            print(f"{cab.name}: {resultado['mensagem']}")
            falhas += resultado["status"] == "erro"
    return 1 if falhas else 0


if __name__ == "__main__":
    raise SystemExit(main())
