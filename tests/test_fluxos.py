import hashlib
from datetime import timedelta
from src.backend.app.core.security import (
    criar_token_acesso,
    decodificar_token_acesso,
    gerar_hash_senha,
    serializer,
    gerar_token_aprovacao,
)
from src.backend.app.models import Usuario


def test_token_expirado():
    assert (
        decodificar_token_acesso(
            criar_token_acesso({"sub": "a@example.com"}, timedelta(seconds=-1))
        )
        is None
    )


def test_reset_uso_unico_revoga_sessao(client, usuario_admin, token_admin, db_session):
    token = serializer.dumps(
        {
            "id": usuario_admin.id,
            "senha": hashlib.sha256(usuario_admin.senha_hash.encode()).hexdigest(),
        },
        salt="recuperacao-senha",
    )
    payload = {"token": token, "senha": "NovaSenhaSegura123"}
    assert client.post("/api/v1/auth/redefinir", json=payload).status_code == 200
    assert client.post("/api/v1/auth/redefinir", json=payload).status_code == 400
    assert (
        client.get(
            "/api/v1/auth/me", headers={"Authorization": f"Bearer {token_admin}"}
        ).status_code
        == 401
    )


def test_aprovacao_get_nao_muda_estado(client, db_session):
    u = Usuario(
        nome="Novo",
        email="novo@example.com",
        senha_hash=gerar_hash_senha("SenhaSegura123"),
        aprovado=False,
    )
    db_session.add(u)
    db_session.commit()
    token = gerar_token_aprovacao(u.id)
    assert (
        client.get("/api/v1/auth/aprovar", params={"token": token}).status_code == 200
    )
    db_session.refresh(u)
    assert not u.aprovado
    assert client.post("/api/v1/auth/aprovar", data={"token": token}).status_code == 200
    assert client.post("/api/v1/auth/aprovar", data={"token": token}).status_code == 409


def test_vendedor_sem_acesso_admin(client, db_session):
    u = Usuario(
        nome="Vendedor",
        email="v@example.com",
        senha_hash=gerar_hash_senha("SenhaSegura123"),
        perfil="vendedor",
        aprovado=True,
    )
    db_session.add(u)
    db_session.commit()
    token = client.post(
        "/api/v1/auth/login", data={"username": u.email, "password": "SenhaSegura123"}
    ).json()["access_token"]
    h = {"Authorization": f"Bearer {token}"}
    assert client.get("/api/v1/usuarios", headers=h).status_code == 403
    assert client.get("/api/v1/cargas", headers=h).status_code == 403
    assert (
        client.post(
            "/api/v1/cargas/excel",
            headers=h,
            files={
                "arquivo_cabecalho": ("a.xlsx", b"x"),
                "arquivo_itens": ("b.xlsx", b"x"),
            },
        ).status_code
        == 403
    )


def test_usuario_nao_desativa_a_si_mesmo(client, token_admin, usuario_admin):
    assert (
        client.patch(
            f"/api/v1/usuarios/{usuario_admin.id}",
            headers={"Authorization": f"Bearer {token_admin}"},
            json={"ativo": False},
        ).status_code
        == 400
    )


def test_recuperacao_envia_email_mockado(client, usuario_admin, mock_email_service):
    r = client.post("/api/v1/auth/recuperar", json={"email": usuario_admin.email})
    assert r.status_code == 200
    assert mock_email_service.await_count == 1


def test_erro_smtp_nao_perde_cadastro(client, db_session, mock_email_service):
    mock_email_service.side_effect = RuntimeError("SMTP indisponível")
    r = client.post(
        "/api/v1/auth/registrar",
        json={"nome": "Novo", "email": "novo@example.com", "senha": "SenhaSegura123"},
    )
    assert r.status_code == 201
    assert "não pôde" in r.json()["mensagem"]
    assert (
        not db_session.query(Usuario).filter_by(email="novo@example.com").one().aprovado
    )
