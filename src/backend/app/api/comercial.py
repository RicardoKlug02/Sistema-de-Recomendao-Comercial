from collections import defaultdict
from datetime import date
from decimal import Decimal
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload
from src.backend.app.core.database import get_db
from src.backend.app.api.deps import get_usuario_atual
from src.backend.app.models import Cliente, Venda, Fabrica, Produto, ItemVenda

router = APIRouter(
    prefix="/comercial", tags=["Comercial"], dependencies=[Depends(get_usuario_atual)]
)


@router.get("/resumo")
def resumo(db: Session = Depends(get_db)):
    mensal = defaultdict(float)
    clientes = defaultdict(float)
    for venda in db.query(Venda).all():
        mensal[venda.data_venda.strftime("%Y-%m")] += float(venda.valor_total)
        clientes[venda.cliente_id] += float(venda.valor_total)
    top = sorted(clientes.items(), key=lambda x: x[1], reverse=True)[:5]
    nomes = {
        c.id: c.razao_social
        for c in db.query(Cliente).filter(Cliente.id.in_([i for i, _ in top])).all()
    }
    return dict(
        faturamento=sum(mensal.values()),
        clientes=db.query(Cliente).count(),
        pedidos=db.query(Venda).count(),
        fabricas=db.query(Fabrica).count(),
        mensal=[dict(mes=m, valor=v) for m, v in sorted(mensal.items())[-12:]],
        top_clientes=[dict(id=i, nome=nomes[i], valor=v) for i, v in top],
    )


@router.get("/produtos")
def produtos(termo: str = "", db: Session = Depends(get_db)):
    q = db.query(Produto)
    if termo.strip():
        q = q.filter(
            Produto.nome.ilike(f"%{termo.strip()}%")
            | Produto.sku.ilike(f"%{termo.strip()}%")
        )
    return [
        dict(id=p.id, nome=p.nome, sku=p.sku)
        for p in q.order_by(Produto.nome).limit(100)
    ]


@router.get("/relatorio")
def relatorio(
    inicio: str = "",
    fim: str = "",
    cliente: str = "",
    categoria: str = "",
    regiao: str = "",
    fabrica: str = "",
    pagina: int = Query(1, ge=1),
    db: Session = Depends(get_db),
):
    q = db.query(Venda).options(joinedload(Venda.cliente), joinedload(Venda.fabrica))
    try:
        de = date.fromisoformat(inicio) if inicio else None
        ate = date.fromisoformat(fim) if fim else None
    except ValueError:
        raise HTTPException(422, "Informe datas válidas.")
    if de and ate and de > ate:
        raise HTTPException(422, "A data inicial deve anteceder a final.")
    if de:
        q = q.filter(Venda.data_venda >= de)
    if ate:
        q = q.filter(Venda.data_venda <= ate)
    if cliente or regiao:
        ids = [
            c.id
            for c in db.query(Cliente).yield_per(200)
            if cliente.casefold() in c.razao_social.casefold()
            and regiao.casefold()
            in " ".join(
                [c.cidade or "", c.micro_regiao or "", c.estado or ""]
            ).casefold()
        ]
        q = q.filter(Venda.cliente_id.in_(ids))
    if fabrica:
        q = q.join(Fabrica).filter(Fabrica.nome_fantasia.ilike(f"%{fabrica}%"))
    # Categoria seleciona itens; não atribui todo o valor de pedidos mistos à categoria.
    valores = None
    if categoria:
        valores = dict(
            db.query(ItemVenda.venda_id, func.sum(ItemVenda.subtotal))
            .join(Produto)
            .filter(Produto.categoria.ilike(f"%{categoria}%"))
            .group_by(ItemVenda.venda_id)
            .all()
        )
        q = q.filter(Venda.id.in_(valores))
    total = q.count()
    ids_valores = q.with_entities(Venda.id, Venda.valor_total).all()
    valor = sum(
        (valores[i] if valores is not None else v for i, v in ids_valores), Decimal(0)
    )
    itens = [
        dict(
            id=v.id,
            numero_pedido=v.numero_pedido,
            data_venda=v.data_venda,
            cliente_id=v.cliente_id,
            cliente=v.cliente.razao_social,
            fabrica=v.fabrica.nome_fantasia,
            valor_total=valores[v.id] if valores is not None else v.valor_total,
        )
        for v in q.order_by(Venda.data_venda.desc(), Venda.id.desc())
        .offset((pagina - 1) * 20)
        .limit(20)
    ]
    return dict(itens=itens, total=total, valor_total=valor)
