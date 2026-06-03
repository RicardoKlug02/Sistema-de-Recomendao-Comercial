# init_db.py (na raiz)
import sys
import os

# Adiciona a pasta raiz ao sys.path para o Python encontrar o pacote 'src'
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from src.backend.app.core.database import engine, Base
from src.backend.app.models.cliente import Cliente
from src.backend.app.models.fabrica import Fabrica
from src.backend.app.models.item_venda import ItemVenda
from src.backend.app.models.produto import Produto
from src.backend.app.models.venda import Venda
from src.backend.app.models.vendedor import Vendedor


def init_db():
    print("Iniciando a criação das tabelas no banco de dados...")
    Base.metadata.create_all(bind=engine)
    print("Tabelas criadas com sucesso!")

if __name__ == "__main__":
    init_db()