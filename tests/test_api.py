def test_rota_publica_healthcheck(client):
    res = client.get("/")
    assert res.status_code == 200
    assert res.json()["status"] == "online"


def test_fluxo_autenticacao_registro_login(client):
    # Cadastro de vendedor pendente de aprovação
    registro_res = client.post(
        "/api/v1/auth/registrar",
        json={
            "nome": "Vendedor Novo",
            "email": "vendedor@teste.com",
            "senha": "senhaSegura123",
        },
    )
    assert registro_res.status_code == 201

    # Tentativa de login antes da aprovação do admin via form OAuth2 -> 403 Forbidden
    login_bloqueado = client.post(
        "/api/v1/auth/login",
        data={"username": "vendedor@teste.com", "password": "senhaSegura123"},
    )
    assert login_bloqueado.status_code in (401, 403)
    assert "pendente de aprovação" in login_bloqueado.json()["detail"]

def test_bloqueio_rotas_sem_token_jwt(client):
    # Tenta consultar busca sem header Authorization -> 401 Unauthorized
    res = client.get("/api/v1/clientes/busca?termo=Mercado")
    assert res.status_code == 401


def test_busca_clientes_com_token_autenticado(client, token_admin):
    headers = {"Authorization": f"Bearer {token_admin}"}
    res = client.get("/api/v1/clientes/busca?termo=Distribuidora", headers=headers)
    assert res.status_code == 200
    assert isinstance(res.json(), list)


def test_upload_bloqueado_para_arquivos_nao_excel(client, token_admin):
    headers = {"Authorization": f"Bearer {token_admin}"}
    files = {
        "arquivo_cabecalho": ("teste.txt", b"arquivo de texto comum", "text/plain"),
        "arquivo_itens": ("itens.txt", b"arquivo de texto comum", "text/plain"),
    }
    res = client.post("/api/v1/cargas/excel", headers=headers, files=files)
    assert res.status_code == 400
    assert "Formato inválido" in res.json()["detail"]