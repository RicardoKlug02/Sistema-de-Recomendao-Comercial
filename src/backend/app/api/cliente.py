from typing import Any, Dict, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from src.backend.app.api.deps import get_db, get_usuario_atual
from src.backend.app.models.usuario import Usuario
from src.backend.app.schemas.cliente import ClienteOptionOut, ClienteDetalhesOut
from src.backend.app.services.associacao_service import AssociacaoService
from src.backend.app.services.cliente_service import ClienteService
from src.backend.app.services.recompra_service import RecompraService

router = APIRouter(prefix="/clientes", tags=["Clientes"])


@router.get("/busca", response_model=List[ClienteOptionOut])
def buscar_clientes(
    termo: str = Query(
        ..., min_length=2, description="Razão Social, Nome Fantasia ou CNPJ/CPF"
    ),
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_usuario_atual),
):
    """Autocomplete rápido para a barra de busca global do React."""
    service = ClienteService(db_session=db)
    return service.buscar_por_termo(termo)


@router.get("/alertas/home", response_model=List[Dict[str, Any]])
def obter_alertas_dashboard(
    limite: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_usuario_atual),
):
    """Carrega os cards da tela inicial com os clientes em risco crítico de churn."""
    service = RecompraService(db_session=db)
    return service.obter_alertas_globais_alto_volume(limite_alertas=limite)


@router.post("/cross-selling", response_model=List[Dict[str, Any]])
def obter_cross_selling(
    produtos_ids: List[int],
    top_n: int = Query(4, ge=1, le=10),
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_usuario_atual),
):
    """Sugestão instantânea de venda casada para itens incluídos em cotações/carrinhos."""
    service = AssociacaoService(db_session=db)
    return service.recomendar_cross_selling(produto_ids=produtos_ids, top_n=top_n)


@router.get("/{cliente_id}", response_model=ClienteDetalhesOut)
def obter_ficha_cliente(
    cliente_id: int,
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_usuario_atual),
):
    """Dossiê 360 do cliente: faturamento recente, ciclo por fábrica, reposições e abandono."""
    service = ClienteService(db_session=db)
    detalhes = service.obter_dossie_cliente(cliente_id)

    if not detalhes:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente não localizado na base.",
        )

    return detalhes


@router.get("")
def listar_clientes(
    termo: str = "",
    pagina: int = Query(1, ge=1),
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_usuario_atual),
):
    from src.backend.app.models.cliente import Cliente
    from src.backend.app.core.security import gerar_blind_index

    termo = termo.strip().casefold()
    encontrados = []
    for c in db.query(Cliente).order_by(Cliente.id).yield_per(200):
        texto = " ".join(
            [
                c.razao_social,
                c.nome_fantasia or "",
                c.cidade or "",
                c.grupo_economico or "",
                c.cnpj_cpf or "",
            ]
        ).casefold()
        if not termo or termo in texto or c.cnpj_hash == gerar_blind_index(termo):
            encontrados.append(c)
    return {
        "total": len(encontrados),
        "itens": [
            ClienteOptionOut.model_validate(c)
            for c in encontrados[(pagina - 1) * 20 : pagina * 20]
        ],
    }


@router.get("/{cliente_id}/vendas")
def historico_cliente(
    cliente_id: int,
    pagina: int = Query(1, ge=1),
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_usuario_atual),
):
    from sqlalchemy.orm import joinedload
    from src.backend.app.models import Cliente, Venda, ItemVenda

    if not db.get(Cliente, cliente_id):
        raise HTTPException(404, "Cliente não encontrado.")
    q = db.query(Venda).filter(Venda.cliente_id == cliente_id)
    total = q.count()
    vendas = (
        q.options(
            joinedload(Venda.fabrica),
            joinedload(Venda.itens).joinedload(ItemVenda.produto),
        )
        .order_by(Venda.data_venda.desc(), Venda.id.desc())
        .offset((pagina - 1) * 20)
        .limit(20)
        .all()
    )
    return {
        "total": total,
        "itens": [
            dict(
                id=v.id,
                numero_pedido=v.numero_pedido,
                data_venda=v.data_venda,
                fabrica=v.fabrica.nome_fantasia,
                valor_total=v.valor_total,
                itens=[
                    dict(
                        id=i.id,
                        nome=i.produto.nome,
                        quantidade=i.quantidade,
                        preco_unitario=i.preco_unitario,
                        subtotal=i.subtotal,
                    )
                    for i in v.itens
                ],
            )
            for v in vendas
        ],
    }
