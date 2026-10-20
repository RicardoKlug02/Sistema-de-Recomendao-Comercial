"""Uma rede é um cliente comercial; IDs e documentos continuam sendo fiscais."""
from sqlalchemy import case
from src.backend.app.models import Cliente, Venda


def normalizar_rede(nome):
    return ' '.join((nome or '').split()).casefold()


def chave_cliente(cliente_id, rede):
    nome = normalizar_rede(rede)
    return f'rede:{nome}' if nome else f'cliente:{cliente_id}'


class IdentidadeCliente:
    def __init__(self, db):
        self.clientes = {c.id: c for c in db.query(Cliente.id, Cliente.razao_social,
            Cliente.grupo_economico, Cliente.micro_regiao, Cliente.estado)}
        representantes = {}
        self.ids = {}
        for cid, c in sorted(self.clientes.items()):
            chave = chave_cliente(cid, c.grupo_economico)
            self.ids[cid] = representantes.setdefault(chave, cid)

    def id(self, fiscal_id):
        return self.ids[fiscal_id]

    def nome(self, fiscal_id):
        c = self.clientes[self.id(fiscal_id)]
        return (c.grupo_economico or '').strip() or c.razao_social

    def fiscais(self, fiscal_id):
        comercial = self.id(fiscal_id)
        return [cid for cid, grupo in self.ids.items() if grupo == comercial]

    def expressao(self):
        # Apenas IDs de redes precisam de CASE; cadastros individuais preservam seu ID.
        mapa = {cid: grupo for cid, grupo in self.ids.items() if cid != grupo}
        return case(mapa, value=Venda.cliente_id, else_=Venda.cliente_id) if mapa else Venda.cliente_id
