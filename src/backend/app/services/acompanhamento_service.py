from sqlalchemy import func
from src.backend.app.models import AcaoAlerta, Usuario


def payload(acao, usuario):
    return {'versao': acao.id, 'situacao': acao.situacao, 'motivo': acao.motivo,
            'proximo_contato': acao.proximo_contato, 'atualizado_em': acao.criado_em,
            'usuario': usuario, 'assinatura': acao.assinatura}


def acompanhamentos(db, identidade):
    ids = db.query(func.max(AcaoAlerta.id)).group_by(AcaoAlerta.cliente_id)
    resultado = {}
    for acao, nome in (db.query(AcaoAlerta,Usuario.nome).join(Usuario,Usuario.id==AcaoAlerta.usuario_id)
                       .filter(AcaoAlerta.id.in_(ids)).order_by(AcaoAlerta.id)):
        resultado[identidade.id(acao.cliente_id)] = payload(acao,nome)
    return resultado
