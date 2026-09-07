from pathlib import Path
import sys

raiz = Path(__file__).resolve().parent.parent
if str(raiz) not in sys.path:
    sys.path.insert(0, str(raiz))

from sqlalchemy.orm import Session
from src.backend.app.core.database import engine
from src.backend.app.core.security import decrypt_data
from src.backend.app.models.cliente import Cliente

with Session(engine) as session:
    clientes = session.query(Cliente).limit(5).all()

    if not clientes:
        print("Nenhum cliente encontrado no banco.")
    else:
        print(f"{'ID':<4} | {'CNPJ/CPF (Hash)':<22} | {'No Banco (Criptografado)':<35} | {'Na Tela (Descriptografado)'}")
        print("-" * 105)
        for c in clientes:
            raw_banco = (c.razao_social[:30] + "...") if c.razao_social and len(c.razao_social) > 30 else (c.razao_social or "")
            nome_real = decrypt_data(c.razao_social)
            print(f"{c.id:<4} | {c.cnpj_cpf:<22} | {raw_banco:<35} | {nome_real}")