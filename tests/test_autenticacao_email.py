import json
from unittest.mock import AsyncMock, patch

import httpx
import pytest
from itsdangerous import URLSafeTimedSerializer

from src.backend.app.core.config import settings
from src.backend.app.core.security import gerar_token_aprovacao, validar_token_aprovacao
from src.backend.app.models.usuario import Usuario

CADASTRO = {"nome": "Pessoa Teste", "email": "pessoa@teste.com", "senha": "senha-segura"}
ROTA = "/api/v1/auth/registrar"


def test_falha_email_permite_retomar_sem_duplicar_conta(client, db_session, mock_email_service):
    mock_email_service.side_effect = TimeoutError("segredo-nao-deve-aparecer")
    resposta = client.post(ROTA, json=CADASTRO)
    assert resposta.status_code == 503
    assert "cadastro está salvo" in resposta.json()["detail"]
    assert "segredo" not in resposta.text
    usuario = db_session.query(Usuario).one()
    assert not usuario.aprovado
    identificador = usuario.id
    hash_original = usuario.senha_hash

    # Outra senha não pode tomar posse do cadastro nem disparar novo e-mail.
    assert client.post(ROTA, json={**CADASTRO, "senha": "outra-senha"}).status_code == 400
    assert mock_email_service.await_count == 1
    mock_email_service.side_effect = None
    assert client.post(ROTA, json={**CADASTRO, "nome": "Não substituir"}).status_code == 201
    db_session.expire_all()
    usuario = db_session.query(Usuario).one()
    assert (usuario.id, usuario.nome, usuario.senha_hash) == (identificador, CADASTRO["nome"], hash_original)
    assert not usuario.aprovado


def test_aprovacao_e_login_com_email_normalizado(client, db_session):
    assert client.post(ROTA, json=CADASTRO).status_code == 201
    usuario = db_session.query(Usuario).one()
    credenciais = {"username": "PESSOA@TESTE.COM", "password": CADASTRO["senha"]}
    assert client.post("/api/v1/auth/login", data=credenciais).status_code == 401
    token = gerar_token_aprovacao(usuario.id)
    assert client.get("/api/v1/auth/aprovar", params={"token": token + "x"}).status_code == 400
    assert client.get("/api/v1/auth/aprovar", params={"token": token}).status_code == 200
    assert client.post("/api/v1/auth/login", data=credenciais).status_code == 200
    assert client.post(ROTA, json=CADASTRO).status_code == 400
    assert client.post("/api/v1/auth/login", data={**credenciais, "password": "incorreta"}).status_code == 401


def test_link_expirado_e_finalidade_incorreta():
    with patch("itsdangerous.timed.time.time", return_value=1000):
        token = gerar_token_aprovacao(1)
    with patch("itsdangerous.timed.time.time", return_value=1000 + 49 * 3600):
        with pytest.raises(ValueError, match="expirado"):
            validar_token_aprovacao(token)
    outro_token = URLSafeTimedSerializer(settings.CHAVE_SERIALIZER).dumps(1, salt="outro-uso")
    with pytest.raises(ValueError, match="inválido"):
        validar_token_aprovacao(outro_token)


def test_configuracao_email_ausente_nao_impede_login(client, usuario_admin, monkeypatch):
    monkeypatch.setattr(settings, "MAIL_FROM", "")
    resposta = client.post(ROTA, json=CADASTRO)
    assert resposta.status_code == 503
    assert client.post("/api/v1/auth/login", data={"username": usuario_admin.email, "password": "admin123"}).status_code == 200


def test_envio_https_e_escape_do_email(client, monkeypatch, mock_email_service):
    monkeypatch.setattr(settings, "EMAIL_PROVEDOR", "resend")
    monkeypatch.setattr(settings, "RESEND_API_KEY", "chave-ficticia")
    resposta = httpx.Response(200, json={"id": "envio-teste"}, request=httpx.Request("POST", "https://api.resend.com/emails"))
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=resposta) as envio:
        assert client.post(ROTA, json={**CADASTRO, "nome": '<b>Teste</b>'}).status_code == 201
    chamada = envio.call_args
    assert chamada.args == ("https://api.resend.com/emails",)
    assert chamada.kwargs["headers"]["Authorization"] == "Bearer chave-ficticia"
    dados = chamada.kwargs["json"]
    assert dados["to"] == [settings.ADMIN_EMAIL]
    assert "https://api.teste.com/api/v1/auth/aprovar?token=" in dados["html"]
    assert "&lt;b&gt;Teste&lt;/b&gt;" in dados["html"]
    assert CADASTRO["senha"] not in json.dumps(dados)
    mock_email_service.assert_not_awaited()


@pytest.mark.parametrize("codigo", [401, 403, 429, 500])
def test_rejeicao_provedor_retorna_503_sem_expor_resposta(client, monkeypatch, codigo):
    monkeypatch.setattr(settings, "EMAIL_PROVEDOR", "resend")
    monkeypatch.setattr(settings, "RESEND_API_KEY", "chave-ficticia")
    resposta = httpx.Response(codigo, json={"message": "detalhe-secreto"}, request=httpx.Request("POST", "https://api.resend.com/emails"))
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=resposta):
        resultado = client.post(ROTA, json=CADASTRO)
    assert resultado.status_code == 503
    assert "detalhe-secreto" not in resultado.text


def test_timeout_https_e_chave_ausente(client, monkeypatch):
    monkeypatch.setattr(settings, "EMAIL_PROVEDOR", "resend")
    monkeypatch.setattr(settings, "RESEND_API_KEY", "")
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as envio:
        assert client.post(ROTA, json=CADASTRO).status_code == 503
        envio.assert_not_awaited()
        monkeypatch.setattr(settings, "RESEND_API_KEY", "chave-ficticia")
        envio.side_effect = httpx.ReadTimeout("tempo esgotado")
        assert client.post(ROTA, json=CADASTRO).status_code == 503
