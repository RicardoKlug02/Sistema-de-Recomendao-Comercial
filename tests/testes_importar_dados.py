import sys
from pathlib import Path
import pandas as pd
import pytest
from src.backend.app.services.excel_service import ExcelService
from src.backend.app.models.cliente import Cliente
import hashlib

from unittest.mock import MagicMock
from src.backend.app.services.excel_service import ExcelService

def test_anonimizacao_dados_cliente():
    # Cria uma sessão simulada para não depender do banco
    mock_db = MagicMock()
    service = ExcelService(db_session=mock_db)
    
    documento_cliente = "123.456.789-00"
    resultado_anonimizado = service._anonimizar(documento_cliente)
    
    # Validações
    assert resultado_anonimizado != documento_cliente
    assert len(resultado_anonimizado) == 64  