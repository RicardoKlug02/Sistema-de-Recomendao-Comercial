import os
import sys

# Adiciona a raiz do projeto ao sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.backend.app.core.database import Base, engine
from src.backend.app.models.cliente import Cliente
from src.backend.app.models.fabrica import Fabrica
from src.backend.app.models.item_venda import ItemVenda
from src.backend.app.models.produto import Produto
from src.backend.app.models.usuario import Usuario
from src.backend.app.models.venda import Venda


def init_db():
    print("Iniciando a criação das tabelas no banco de dados...")
    Base.metadata.create_all(bind=engine)
    print("Tabelas criadas com sucesso!")


if __name__ == "__main__":
    init_db()