from pathlib import Path
import tempfile
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, Query
from sqlalchemy.orm import Session
from src.backend.app.api.deps import get_db, get_usuario_admin
from src.backend.app.models.usuario import Usuario
from src.backend.app.models.importacao import Importacao
from src.backend.app.services.excel_service import ExcelService

router = APIRouter(prefix="/cargas", tags=["Cargas e Importação"])
LIMITE = 10 * 1024 * 1024


def copiar_limitado(arquivo, caminho):
    if not arquivo.filename or Path(arquivo.filename).suffix.lower() not in (
        ".xlsx",
        ".xls",
    ):
        raise HTTPException(400, "Formato inválido. Envie XLS ou XLSX.")
    tamanho = 0
    with open(caminho, "wb") as saida:
        while bloco := arquivo.file.read(64 * 1024):
            tamanho += len(bloco)
            if tamanho > LIMITE:
                raise HTTPException(413, "Cada planilha deve ter no máximo 10 MB.")
            saida.write(bloco)
    if tamanho == 0:
        raise HTTPException(422, "Planilha vazia.")


@router.post("/excel")
def upload_planilhas_vendas(
    arquivo_cabecalho: UploadFile = File(...),
    arquivo_itens: UploadFile = File(...),
    permitir_atualizacao: bool = Form(False),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_usuario_admin),
):
    # Handler síncrono roda no pool de threads; Pandas não bloqueia o event loop.
    nomes = " + ".join(
        Path(a.filename or "arquivo").name[:240]
        for a in [arquivo_cabecalho, arquivo_itens]
    )
    try:
        with tempfile.TemporaryDirectory() as pasta:
            cab, itens = Path(pasta) / "pedidos", Path(pasta) / "itens"
            copiar_limitado(arquivo_cabecalho, cab)
            copiar_limitado(arquivo_itens, itens)
            resultado = ExcelService(db).importar_processo_completo(
                cab, itens, permitir_atualizacao=permitir_atualizacao, commit=False
            )
            db.add(
                Importacao(
                    arquivos=nomes,
                    usuario=usuario.email,
                    status=resultado["status"],
                    mensagem=resultado["mensagem"],
                )
            )
            db.commit()
            if resultado["status"] == "erro":
                raise HTTPException(422, resultado["mensagem"])
            return resultado
    finally:
        arquivo_cabecalho.file.close()
        arquivo_itens.file.close()


@router.get("")
def historico(
    pagina: int = Query(1, ge=1),
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_usuario_admin),
):
    q = db.query(Importacao)
    return {
        "total": q.count(),
        "itens": [
            dict(
                id=i.id,
                arquivos=i.arquivos,
                usuario=i.usuario,
                status=i.status,
                mensagem=i.mensagem,
                criado_em=i.criado_em,
            )
            for i in q.order_by(Importacao.id.desc())
            .offset((pagina - 1) * 20)
            .limit(20)
        ],
    }
