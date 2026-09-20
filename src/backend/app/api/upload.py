import os
import shutil
import tempfile
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from src.backend.app.api.deps import get_db, get_usuario_admin
from src.backend.app.models.usuario import Usuario
from src.backend.app.services.excel_service import ExcelService

router = APIRouter(prefix="/cargas", tags=["Cargas e Importação"])


@router.post("/excel", status_code=status.HTTP_200_OK)
async def upload_planilhas_vendas(
    arquivo_cabecalho: UploadFile = File(..., description="Planilha de pedidos/cabeçalho"),
    arquivo_itens: UploadFile = File(..., description="Planilha de itens faturados por produto"),
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_usuario_admin),  # Apenas admins podem subir cargas
):
    """Recebe as duas planilhas do ERP, processa em lote e atualiza a base."""
    for arq in [arquivo_cabecalho, arquivo_itens]:
        if not arq.filename.endswith((".xlsx", ".xls")):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Formato inválido para '{arq.filename}'. Envie planilhas Excel (.xlsx).",
            )

    with tempfile.TemporaryDirectory() as temp_dir:
        path_cab = os.path.join(temp_dir, "cabecalho.xlsx")
        path_itens = os.path.join(temp_dir, "itens.xlsx")

        with open(path_cab, "wb") as f_cab:
            shutil.copyfileobj(arquivo_cabecalho.file, f_cab)

        with open(path_itens, "wb") as f_itens:
            shutil.copyfileobj(arquivo_itens.file, f_itens)

        service = ExcelService(db_session=db)
        resultado = service.importar_processo_completo(path_cab=path_cab, path_itens=path_itens)

        if resultado.get("status") == "erro":
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=resultado.get("mensagem"),
            )

    return resultado