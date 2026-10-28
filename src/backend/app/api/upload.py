import json
import logging
import os
import tempfile
import hashlib
from pathlib import Path
from typing import Literal
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from sqlalchemy.orm import Session
from src.backend.app.api.deps import get_db, get_usuario_admin, get_usuario_atual
from src.backend.app.core.config import settings
from src.backend.app.models import Usuario, Importacao
from src.backend.app.services.excel_service import ExcelService

router = APIRouter(prefix="/cargas", tags=["Cargas e Importação"])


def _copiar(arquivo, destino):
    extensao = os.path.splitext(arquivo.filename or "")[1].lower()
    if extensao not in (".xls", ".xlsx"):
        raise HTTPException(400, "Formato inválido. Envie planilhas Excel (.xlsx ou .xls).")
    tamanho = 0
    with open(destino, "wb") as saida:
        while bloco := arquivo.file.read(1024 * 1024):
            tamanho += len(bloco)
            if tamanho > settings.MAX_UPLOAD_MB * 1024 * 1024:
                raise HTTPException(413, f"Cada planilha deve ter no máximo {settings.MAX_UPLOAD_MB} MB.")
            saida.write(bloco)
    if tamanho == 0:
        raise HTTPException(400, "Planilha vazia.")


def _resultado(carga):
    avisos = json.loads(carga.avisos_json)
    resumo = json.loads(carga.resumo_json or "{}")
    return {"id": carga.id, "arquivo": carga.arquivo, "arquivo_itens": carga.arquivo_itens,
            "usuario": carga.usuario, "data": carga.criado_em.date().isoformat(),
            "processados": carga.processados, "adicionados": carga.adicionados,
            "atualizados": carga.atualizados, "itens": carga.itens,
            "pedidos_sem_itens": carga.pedidos_sem_itens, "avisos": avisos, "erros": 0,
            "modo": resumo.get("modo", "atualizar"), "mes": resumo.get("mes"),
            "excluidos": resumo.get("excluidos", 0), "itens_removidos": resumo.get("itens_removidos", 0),
            "quantidades_reduzidas": resumo.get("quantidades_reduzidas", 0)}


@router.get("/historico")
def historico(db: Session = Depends(get_db), _: Usuario = Depends(get_usuario_atual)):
    return [_resultado(c) for c in db.query(Importacao).order_by(Importacao.id.desc()).limit(100).all()]


@router.post("/conferir")
def conferir_planilhas(arquivo_cabecalho: UploadFile = File(...), arquivo_itens: UploadFile = File(...),
                       modo: Literal["atualizar", "sincronizar_mes"] = Form("atualizar"), mes: str | None = Form(None),
                       db: Session = Depends(get_db), usuario: Usuario = Depends(get_usuario_admin)):
    return _processar(arquivo_cabecalho, arquivo_itens, db, usuario, conferir=True, modo=modo, mes=mes)


@router.post("/excel")
def upload_planilhas_vendas(arquivo_cabecalho: UploadFile = File(...), arquivo_itens: UploadFile = File(...),
                            token_conferencia: str = Form(...), vendas_comissao: bool = Form(...),
                            modo: Literal["atualizar", "sincronizar_mes"] = Form("atualizar"), mes: str | None = Form(None),
                            confirmar_sincronizacao: bool = Form(False),
                            db: Session = Depends(get_db), usuario: Usuario = Depends(get_usuario_admin)):
    if not vendas_comissao:
        raise HTTPException(422, "Confirme que os arquivos contêm somente vendas efetivadas que geram comissão.")
    if modo == "sincronizar_mes" and not confirmar_sincronizacao:
        raise HTTPException(422, "Confirme que o mês está completo e autorize a sincronização dos pedidos e itens.")
    return _processar(arquivo_cabecalho, arquivo_itens, db, usuario, token=token_conferencia, modo=modo, mes=mes)


def _processar(arquivo_cabecalho, arquivo_itens, db, usuario, conferir=False, token=None, modo="atualizar", mes=None):
    try:
        with tempfile.TemporaryDirectory() as pasta:
            cab = os.path.join(pasta, "cab" + os.path.splitext(arquivo_cabecalho.filename or "")[1].lower())
            itens = os.path.join(pasta, "itens" + os.path.splitext(arquivo_itens.filename or "")[1].lower())
            _copiar(arquivo_cabecalho, cab)
            _copiar(arquivo_itens, itens)
            service = ExcelService(db)
            service._periodo_sincronizacao(modo, mes)
            df_cab = service._limpar_excel_cabecalho(cab, permitir_vazio=modo == "sincronizar_mes")
            df_itens = service._limpar_excel_produtos(itens)
            if not conferir and db.bind.dialect.name == "postgresql":
                from sqlalchemy import text
                if not db.execute(text("SELECT pg_try_advisory_xact_lock(20260929)")).scalar():
                    raise HTTPException(409, "Outra importação está em andamento. Aguarde a conclusão antes de enviar novamente.")
            resumo = service.conferir(df_cab, df_itens, modo=modo, mes=mes)
            arquivos = [hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in (cab, itens)]
            dados_token = {"arquivos": arquivos, "usuario": usuario.id, "estado": resumo.pop("estado"),
                           "modo": modo, "mes": mes}
            assinatura = URLSafeTimedSerializer(settings.SECRET_KEY, salt="conferencia-importacao")
            if conferir:
                return {**resumo, "token_conferencia": assinatura.dumps(dados_token)}
            try:
                conferido = assinatura.loads(token, max_age=1800)
            except (BadSignature, SignatureExpired):
                raise HTTPException(409, "A conferência expirou ou é inválida. Confira novamente as planilhas.")
            if conferido != dados_token:
                raise HTTPException(409, "Os arquivos ou dados mudaram desde a conferência. Confira novamente antes de importar.")
            # Guarda os pedidos excluídos e seus itens para rastreabilidade da carga.
            removidos = service._pedidos_ausentes(service._preparar_carga(df_cab, df_itens, modo, mes)[0], modo, mes)
            from src.backend.app.models import ItemVenda
            ids_removidos = [v.id for v in removidos]
            itens_removidos = {}
            for item in db.query(ItemVenda).filter(ItemVenda.venda_id.in_(ids_removidos)).all():
                itens_removidos.setdefault(item.venda_id, []).append({
                    "produto_id": item.produto_id, "quantidade": item.quantidade, "preco_unitario": item.preco_unitario})
            auditoria = [{"id": v.id, "pedido": v.numero_pedido, "fabrica_id": v.fabrica_id,
                          "cliente_id": v.cliente_id, "vendedor_id": v.vendedor_id,
                          "data": v.data_venda.isoformat(), "valor_total": v.valor_total,
                          "itens": itens_removidos.get(v.id, [])} for v in removidos]
            resultado = service._validar_e_salvar(df_cab, df_itens, commit=False, modo=modo, mes=mes)
            resumo_carga = {k: resumo[k] for k in ("modo", "mes", "excluidos", "itens_removidos", "quantidades_reduzidas")}
            resumo_carga["pedidos_excluidos"] = auditoria
            carga = Importacao(arquivo=os.path.basename(arquivo_cabecalho.filename),
                                arquivo_itens=os.path.basename(arquivo_itens.filename), usuario=usuario.email,
                                avisos_json=json.dumps(resultado["avisos"], ensure_ascii=False),
                                resumo_json=json.dumps(resumo_carga, ensure_ascii=False),
                                **{k: resultado[k] for k in ("processados", "adicionados", "atualizados", "itens", "pedidos_sem_itens")})
            db.add(carga)
            db.commit()
            db.refresh(carga)
            return {"status": "sucesso", "mensagem": resultado["mensagem"], **_resultado(carga)}
    except HTTPException:
        db.rollback()
        raise
    except (ValueError, KeyError, ImportError) as exc:
        db.rollback()
        raise HTTPException(422, str(exc))
    except Exception:
        db.rollback()
        logging.getLogger(__name__).exception("Falha ao importar planilhas.")
        raise HTTPException(500, "Não foi possível concluir a importação. Nenhuma alteração desta carga foi salva.")
    finally:
        arquivo_cabecalho.file.close()
        arquivo_itens.file.close()
