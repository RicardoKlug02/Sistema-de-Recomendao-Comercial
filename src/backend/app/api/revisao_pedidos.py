from typing import Literal
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, model_validator
from sqlalchemy import func
from sqlalchemy.orm import Session
from src.backend.app.api.deps import get_db, get_usuario_admin
from src.backend.app.models import Cliente, Fabrica, RevisaoPedido, Usuario, Venda
from src.backend.app.services.revisao_pedido_service import registrar_revisao


router = APIRouter(prefix='/cargas/pedidos', tags=['Revisão de pedidos'],
                   dependencies=[Depends(get_usuario_admin)])
Classificacao = Literal['NAO_REVISADO', 'VENDA_DIRETA', 'VENDA_COM_ITENS', 'AJUSTE_COMISSIONADO', 'BONIFICACAO', 'DUPLICIDADE', 'OUTRO_TIPO']


class DecisaoPedido(BaseModel):
    classificacao: Classificacao
    motivo: str = Field(min_length=5, max_length=1000)
    evidencia: str = Field('', max_length=1000)
    versao: int = Field(0, ge=0)

    @model_validator(mode='after')
    def validar(self):
        self.motivo, self.evidencia = self.motivo.strip(), self.evidencia.strip()
        if len(self.motivo) < 5:
            raise ValueError('Descreva o motivo da classificação.')
        if self.classificacao == 'VENDA_DIRETA' and len(self.evidencia) < 5:
            raise ValueError('Informe a referência que confirma a venda direta: pedido da fábrica, documento ou contato responsável.')
        return self


@router.get('')
def listar(pedido: str = '', classificacao: Classificacao | Literal[''] | None = 'NAO_REVISADO',
           somente_sem_itens: bool = True, fabrica_id: int | None = None,
           pagina: int = Query(1, ge=1), limite: int = Query(25, ge=1, le=100),
           db: Session = Depends(get_db)):
    q = (db.query(Venda, Cliente, Fabrica.nome_fantasia).select_from(Venda)
         .join(Cliente, Cliente.id == Venda.cliente_id).join(Fabrica, Fabrica.id == Venda.fabrica_id)
         .execution_options(incluir_vendas_excluidas=True))
    if pedido.strip(): q = q.filter(Venda.numero_pedido == pedido.strip())
    if classificacao: q = q.filter(Venda.classificacao == classificacao)
    if somente_sem_itens: q = q.filter(~Venda.itens.any())
    if fabrica_id is not None: q = q.filter(Venda.fabrica_id == fabrica_id)
    total = q.count()
    registros = q.order_by(Venda.data_venda.desc(), Venda.id.desc()).offset((pagina-1)*limite).limit(limite).all()
    ids = [v.id for v, _, _ in registros]
    ultimas = {vid: versao for vid, versao in db.query(RevisaoPedido.venda_id, func.max(RevisaoPedido.id))
               .filter(RevisaoPedido.venda_id.in_(ids)).group_by(RevisaoPedido.venda_id)}
    return {'total': total, 'itens': [{'id': v.id, 'pedido': v.numero_pedido, 'data': v.data_venda,
        'cliente': c.razao_social, 'cnpj_cpf': c.cnpj_cpf, 'rede': c.grupo_economico, 'fabrica': f,
        'valor': v.valor_total, 'classificacao': v.classificacao, 'considerar_analises': v.considerar_analises, 'nova_compra': v.nova_compra,
        'versao': ultimas.get(v.id, 0)} for v, c, f in registros]}


@router.post('/{venda_id}/revisao')
def revisar(venda_id: int, entrada: DecisaoPedido, db: Session = Depends(get_db),
            usuario: Usuario = Depends(get_usuario_admin)):
    venda = (db.query(Venda).execution_options(incluir_vendas_excluidas=True)
             .filter(Venda.id == venda_id).with_for_update().first())
    if venda is None: raise HTTPException(404, 'Pedido não encontrado.')
    versao = db.query(func.max(RevisaoPedido.id)).filter(RevisaoPedido.venda_id == venda.id).scalar() or 0
    if versao != entrada.versao:
        raise HTTPException(409, 'Outro usuário revisou este pedido. Atualize a lista antes de salvar.')
    if entrada.classificacao == 'VENDA_COM_ITENS' and not venda.itens:
        raise HTTPException(422, 'O pedido não tem itens registrados. Corrija a importação ou valide a venda direta.')
    if entrada.classificacao in ('VENDA_DIRETA', 'AJUSTE_COMISSIONADO') and venda.itens:
        raise HTTPException(422, 'Este pedido tem itens registrados. Classifique como venda com itens.')
    evento = registrar_revisao(db, venda, entrada.classificacao, entrada.motivo, entrada.evidencia, usuario.id)
    db.commit(); db.refresh(evento)
    return {'id': venda.id, 'versao': evento.id, 'classificacao': venda.classificacao,
            'considerar_analises': venda.considerar_analises, 'nova_compra': venda.nova_compra}


@router.get('/{venda_id}/historico')
def historico(venda_id: int, db: Session = Depends(get_db)):
    return [{'id': r.id, 'anterior': r.classificacao_anterior, 'classificacao': r.classificacao,
             'motivo': r.motivo, 'evidencia': r.evidencia, 'usuario': nome or 'Correção técnica autorizada', 'data': r.criado_em}
            for r, nome in db.query(RevisaoPedido, Usuario.nome).outerjoin(Usuario, Usuario.id == RevisaoPedido.usuario_id)
            .filter(RevisaoPedido.venda_id == venda_id).order_by(RevisaoPedido.id.desc()).limit(50)]
