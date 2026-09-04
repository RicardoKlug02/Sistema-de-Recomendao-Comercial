import os
import sys
from pathlib import Path
sys.path.insert(0, os.getcwd())    
import pandas as pd
import pytest
from sqlalchemy.orm import Session
from src.backend.app.core.database import engine
from src.backend.app.models.fabrica import Fabrica
from src.backend.app.models.produto import Produto
from src.backend.app.services.excel_service import ExcelService
import hashlib
from unittest.mock import MagicMock
from src.backend.app.services.excel_service import ExcelService

def test_conexao_e_modelos():
    print("\nIniciando teste de conexão e operações no banco...")

    with Session(engine) as session:
        try:
            print("- Inserindo fábrica de teste...")
            fabrica_teste = Fabrica(
                nome_fantasia="Fábrica Teste LTDA", cnpj="99.999.999/0001-99"
            )
            session.add(fabrica_teste)
            session.flush()

            print("- Inserindo produto vinculado...")
            produto_teste = Produto(
                nome="Produto Teste Alpha",
                sku="SKU-TEST-001",
                fabrica_id=fabrica_teste.id,
            )
            session.add(produto_teste)
            session.commit()
            print("  ✓ Registros persistidos no banco.")

            print("- Consultando os registros gravados...")
            prod_consultado = (
                session.query(Produto)
                .filter(Produto.sku == "SKU-TEST-001")
                .first()
            )
            assert (
                prod_consultado is not None
            ), "Falha: produto não foi encontrado no banco."
            assert prod_consultado.fabrica_id == fabrica_teste.id
            print(
                f"  ✓ Consulta OK: ID {prod_consultado.id} | {prod_consultado.nome} (Fábrica ID: {prod_consultado.fabrica_id})"
            )

            print("- Limpando dados de teste...")
            session.delete(prod_consultado)
            session.delete(fabrica_teste)
            session.commit()
            print("  ✓ Registros removidos com sucesso.")

        except Exception as e:
            session.rollback()
            pytest.fail(f"O teste falhou com o erro: {e}")

def test_anonimizacao_dados_cliente():
    # Cria uma sessão simulada para não depender do banco
    mock_db = MagicMock()
    service = ExcelService(db_session=mock_db)
    
    documento_cliente = "123.456.789-00"
    resultado_anonimizado = service._anonimizar(documento_cliente)
    
    # Validações
    assert resultado_anonimizado != documento_cliente
    assert len(resultado_anonimizado) == 64  