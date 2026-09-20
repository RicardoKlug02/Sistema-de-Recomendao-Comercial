import sys
from pathlib import Path

raiz = Path(__file__).resolve().parent.parent
if str(raiz) not in sys.path:
    sys.path.insert(0, str(raiz))

from sqlalchemy.orm import Session
from src.backend.app.core.database import engine
from src.backend.app.services.usuario_service import UsuarioService

with Session(engine) as session:
    service = UsuarioService(db_session=session)

    email = "usuario@empresa.com"
    senha = "senha123"

    user = service.buscar_por_email(email)
    if user:
        print(f"Usuário {email} já existe (ID: {user.id}).")
    else:
        novo = service.criar_usuario(
            nome="Ricardo Klug",
            email="rick.nklug@gmail.com",
            senha_plana="1234567",
        )
        print(f"Usuário criado com sucesso! ID: {novo.id} | Email: {novo.email}")