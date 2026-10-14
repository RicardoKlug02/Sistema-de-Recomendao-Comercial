from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session
from src.backend.app.api.deps import get_db, get_usuario_atual
from src.backend.app.services.relatorios_service import RelatoriosService

router = APIRouter(prefix="/relatorios", tags=["Relatórios"], dependencies=[Depends(get_usuario_atual)])


@router.get("/redes")
def redes(db: Session = Depends(get_db)):
    return RelatoriosService(db).redes()


@router.get("/produtos-rede")
def produtos_rede(rede: str = Query(..., min_length=1), fabrica_id: int | None = None,
                  db: Session = Depends(get_db)):
    try:
        return RelatoriosService(db).produtos_rede(rede, fabrica_id)
    except ValueError as exc:
        raise HTTPException(422, str(exc))


@router.get("/produtos-rede/pdf")
def produtos_rede_pdf(rede: str = Query(..., min_length=1), fabrica_id: int | None = None,
                      db: Session = Depends(get_db)):
    from src.backend.app.services.pdf_service import pdf_produtos_rede
    dados = produtos_rede(rede, fabrica_id, db)
    return Response(pdf_produtos_rede(dados), media_type="application/pdf",
                    headers={"Content-Disposition": 'attachment; filename="produtos-da-rede.pdf"', "Cache-Control": "no-store"})
