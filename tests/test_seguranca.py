import pytest
from datetime import timedelta
from src.backend.app.core.security import (
    gerar_hash_senha,
    verificar_senha,
    encrypt_data,
    decrypt_data,
    criar_token_acesso,
    decodificar_token_acesso,
    gerar_token_aprovacao,
    validar_token_aprovacao,
    gerar_blind_index,
)


def test_hash_e_verificacao_senha():
    senha = "SenhaForteSegura@2026"
    hash_senha = gerar_hash_senha(senha)
    assert hash_senha != senha
    assert verificar_senha(senha, hash_senha) is True
    assert verificar_senha("SenhaIncorreta", hash_senha) is False


def test_limite_bcrypt_72_bytes():
    senha_longa = "a" * 150
    hash_senha = gerar_hash_senha(senha_longa)
    assert verificar_senha(senha_longa, hash_senha) is True


def test_criptografia_simetrica_fernet():
    texto_original = "Supermercado Exemplo LTDA - CNPJ 12.345.678/0001-90"
    cifrado = encrypt_data(texto_original)
    assert cifrado != texto_original
    decifrado = decrypt_data(cifrado)
    assert decifrado == texto_original


def test_blind_index_determinismo_e_higienizacao():
    # Deve gerar o mesmo hash independente de pontos, traços ou barras
    cnpj_formatado = "12.345.678/0001-99"
    cnpj_limpo = "12345678000199"
    
    hash_1 = gerar_blind_index(cnpj_formatado)
    hash_2 = gerar_blind_index(cnpj_limpo)
    
    assert hash_1 == hash_2
    assert len(hash_1) == 64  # SHA256 hex
    assert gerar_blind_index(None) is None


def test_jwt_expiracao_e_adulteracao():
    payload = {"sub": "teste@empresa.com", "perfil": "vendedor"}
    token = criar_token_acesso(payload, expira_em=timedelta(minutes=5))
    decodificado = decodificar_token_acesso(token)
    assert decodificado["sub"] == "teste@empresa.com"
    
    token_invalido = token[:-4] + "fake"
    assert decodificar_token_acesso(token_invalido) is None


def test_token_aprovacao_email():
    usuario_id = 42
    token = gerar_token_aprovacao(usuario_id)
    assert validar_token_aprovacao(token, max_horas=1) == usuario_id

    with pytest.raises(ValueError, match="inválido ou corrompido"):
        validar_token_aprovacao(token + "corrompido")