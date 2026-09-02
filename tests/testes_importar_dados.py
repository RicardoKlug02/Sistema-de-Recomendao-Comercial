import pandas as pd
import pytest
from src.backend.app.services.excel_service import ExcelService
from src.backend.app.models.cliente import Cliente
import hashlib

def test_anonimizacao_dados_cliente(session):
    # Setup: Criar service e dados originais sensíveis
    service = ExcelService(session)
    nome_original = "Empresa Exemplo LTDA"
    cnpj_original = "12.345.678/0001-99"
    
    # Criar um arquivo fake com esses dados
    caminho_teste = "dados_teste.xlsx"
    pd.DataFrame({
        'nome': [nome_original],
        'cnpj_cpf': [cnpj_original],
        'segmento': ['Construção']
    }).to_excel(caminho_teste, index=False)
    
    # Executar a importação
    service.importar_clientes_de_excel(caminho_teste)
    
    # Validação: Buscar o cliente no banco
    cliente_salvo = session.query(Cliente).first()
    
    # O nome salvo deve ter sido transformado em algo genérico ou hash
    assert cliente_salvo.nome != nome_original
    assert nome_original not in cliente_salvo.nome
    
    # Verificar se o hash está presente e não o CNPJ puro
    # Se salvamos o hash no banco, ele deve ser uma string longa (SHA256 tem 64 caracteres)
    assert len(cliente_salvo.id_anonimo) == 64
    assert cliente_salvo.id_anonimo != cnpj_original