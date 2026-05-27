from fastapi import APIRouter
from app.schemas.cliente import ClienteResponse

router = APIRouter()

@router.get("/api/clientes", response_model=list[ClienteResponse])
def listar_clientes():
    # Aqui você buscaria no banco com SQLAlchemy
    # return db.query(Cliente).all()
    return [
        {"id": 1, "nome": "Cliente Teste", "segmento": "Elétrico", "cidade": "Indaial", "estado": "SC"}
    ]