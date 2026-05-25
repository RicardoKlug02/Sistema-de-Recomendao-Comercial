# src/backend/app/models/__init__.py
from app.core.database import Base 
from .cliente import Cliente
from .vendedor import Vendedor
from .fabrica import Fabrica
from .produto import Produto
from .venda import Venda
from .item_venda import ItemVenda