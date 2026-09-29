from decimal import Decimal
import pandas as pd
import pytest
from src.backend.app.services.excel_service import ExcelService
from src.backend.app.models import Venda, ItemVenda, Fabrica, Cliente, Produto


def planilhas(tmp_path, pedidos=None, itens=None):
    pedidos = (
        pedidos
        if pedidos is not None
        else [
            dict(
                pedido="P1",
                cnpj_cpf="11222333000144",
                cliente="Cliente Teste",
                fabrica="Indústria A",
                data="01/01/2026",
                valor_total="20,00",
                cidade="Blumenau",
                estado="SC",
            )
        ]
    )
    itens = (
        itens
        if itens is not None
        else [
            dict(
                pedido="P1",
                sku="SKU-10U",
                nome_produto="Produto teste",
                quantidade=2,
                preco_unitario="10,00",
                categoria="Elétrica",
            )
        ]
    )
    cab, prod = tmp_path / "pedidos.xlsx", tmp_path / "itens.xlsx"
    pd.DataFrame(pedidos).to_excel(cab, index=False)
    pd.DataFrame(itens).to_excel(prod, index=False)
    return cab, prod


def test_importacao_real_idempotente_e_cifrada(db_session, tmp_path):
    cab, itens = planilhas(tmp_path)
    service = ExcelService(db_session)
    assert service.importar_processo_completo(cab, itens)["adicionados"] == 1
    assert service.importar_processo_completo(cab, itens)["inalterados"] == 1
    assert db_session.query(Venda).count() == db_session.query(ItemVenda).count() == 1
    assert db_session.query(Produto).one().sku == "SKU-10U"
    assert db_session.query(Cliente).one().cidade == "Blumenau"
    from sqlalchemy import text

    cifrado = db_session.execute(text("select razao_social from clientes")).scalar()
    assert cifrado.startswith("gAAAA") and "Cliente Teste" not in cifrado


@pytest.mark.parametrize(
    "campo,valor",
    [
        ("data", "31/02/2026"),
        ("data", ""),
        ("valor_total", "invalido"),
        ("fabrica", ""),
        ("cnpj_cpf", "123"),
        ("valor_total", "21,00"),
    ],
)
def test_cabecalho_invalido_nao_grava(campo, valor, db_session, tmp_path):
    cab, prod = planilhas(tmp_path)
    dados = pd.read_excel(cab, dtype=str).fillna("").to_dict("records")
    dados[0][campo] = valor
    cab, prod = planilhas(tmp_path, pedidos=dados)
    r = ExcelService(db_session).importar_processo_completo(cab, prod)
    assert r["status"] == "erro"
    assert db_session.query(Venda).count() == db_session.query(Cliente).count() == 0


@pytest.mark.parametrize(
    "campo,valor",
    [
        ("quantidade", "1,5"),
        ("quantidade", 0),
        ("preco_unitario", -1),
        ("pedido", "ORFAO"),
        ("subtotal", "999"),
        ("sku", ""),
    ],
)
def test_item_invalido_nao_grava(campo, valor, db_session, tmp_path):
    cab, prod = planilhas(tmp_path)
    itens = pd.read_excel(prod).to_dict("records")
    itens[0][campo] = valor
    cab, prod = planilhas(tmp_path, itens=itens)
    assert (
        ExcelService(db_session).importar_processo_completo(cab, prod)["status"]
        == "erro"
    )
    assert db_session.query(Venda).count() == 0


def test_atualizacao_exige_opt_in_e_preserva_em_erro(db_session, tmp_path):
    service = ExcelService(db_session)
    cab, prod = planilhas(tmp_path)
    assert service.importar_processo_completo(cab, prod)["status"] == "sucesso"
    itens = pd.read_excel(prod).to_dict("records")
    itens[0]["preco_unitario"] = 20
    pedidos = pd.read_excel(cab, dtype=str).to_dict("records")
    pedidos[0]["valor_total"] = 40
    cab, prod = planilhas(tmp_path, pedidos, itens)
    assert service.importar_processo_completo(cab, prod)["status"] == "erro"
    assert db_session.query(Venda).one().valor_total == Decimal("20")
    assert (
        service.importar_processo_completo(cab, prod, permitir_atualizacao=True)[
            "atualizados"
        ]
        == 1
    )
    assert db_session.query(ItemVenda).one().preco_unitario == Decimal("20")


def test_nao_remove_produtos_existentes(db_session, tmp_path):
    service = ExcelService(db_session)
    cab, prod = planilhas(tmp_path)
    itens = pd.read_excel(prod).to_dict("records")
    itens[0]["quantidade"] = 1
    itens.append({**itens[0], "sku": "OUTRO"})
    cab, prod = planilhas(tmp_path, itens=itens)
    assert service.importar_processo_completo(cab, prod)["status"] == "sucesso"
    cab, prod = planilhas(tmp_path)
    assert (
        service.importar_processo_completo(cab, prod, permitir_atualizacao=True)[
            "status"
        ]
        == "erro"
    )
    assert db_session.query(ItemVenda).count() == 2


def test_fabrica_correta_e_rollback_conflito(db_session, tmp_path):
    db_session.add(Fabrica(nome_fantasia="Outra fábrica preexistente"))
    db_session.commit()
    cab, prod = planilhas(tmp_path)
    service = ExcelService(db_session)
    assert service.importar_processo_completo(cab, prod)["status"] == "sucesso"
    assert db_session.query(Venda).one().fabrica.nome_fantasia == "Indústria A"
    pedidos = pd.read_excel(cab, dtype=str).to_dict("records")
    pedidos[0].update(pedido="P2", fabrica="Indústria B")
    itens = pd.read_excel(prod).to_dict("records")
    itens[0]["pedido"] = "P2"
    cab, prod = planilhas(tmp_path, pedidos, itens)
    assert service.importar_processo_completo(cab, prod)["status"] == "erro"
    assert db_session.query(Fabrica).count() == 2
    assert db_session.query(Venda).count() == 1


def test_upload_completo_e_historico(client, token_admin, tmp_path):
    cab, prod = planilhas(tmp_path)
    headers = {"Authorization": f"Bearer {token_admin}"}
    with cab.open("rb") as a, prod.open("rb") as b:
        res = client.post(
            "/api/v1/cargas/excel",
            headers=headers,
            files={
                "arquivo_cabecalho": ("PEDIDOS.XLSX", a),
                "arquivo_itens": ("ITENS.XLSX", b),
            },
        )
    assert res.status_code == 200, res.text
    assert client.get("/api/v1/cargas", headers=headers).json()["total"] == 1
    c = client.get("/api/v1/clientes", headers=headers).json()["itens"][0]
    ficha = client.get(f"/api/v1/clientes/{c['id']}", headers=headers)
    assert ficha.status_code == 200, ficha.text
    assert ficha.json()["cidade"] == "Blumenau"
    assert (
        client.get("/api/v1/comercial/resumo", headers=headers).json()["faturamento"]
        == 20
    )
    relatorio = client.get(
        "/api/v1/comercial/relatorio?categoria=Elétrica", headers=headers
    )
    assert relatorio.status_code == 200, relatorio.text
    assert float(relatorio.json()["valor_total"]) == 20


def test_arquivo_falso_e_vazio(client, token_admin):
    for conteudo in [b"nao sou excel", b""]:
        r = client.post(
            "/api/v1/cargas/excel",
            headers={"Authorization": f"Bearer {token_admin}"},
            files={
                "arquivo_cabecalho": ("fake.xlsx", conteudo),
                "arquivo_itens": ("fake.xlsx", conteudo),
            },
        )
        assert r.status_code == 422


def test_arredondamento_erp_preserva_subtotal(db_session, tmp_path):
    cab, prod = planilhas(tmp_path)
    pedidos = pd.read_excel(cab, dtype=str).to_dict("records")
    pedidos[0]["valor_total"] = "2381,40"
    itens = pd.read_excel(prod).to_dict("records")
    itens[0].update(quantidade=25, preco_unitario="95,26", subtotal="2381,40")
    cab, prod = planilhas(tmp_path, pedidos, itens)
    service = ExcelService(db_session)
    assert service.importar_processo_completo(cab, prod)["status"] == "sucesso"
    assert db_session.query(ItemVenda).one().subtotal == Decimal("2381.40")
    assert db_session.query(Venda).one().valor_total == Decimal("2381.40")
    assert service.importar_processo_completo(cab, prod)["inalterados"] == 1


def test_limite_upload_antes_do_parser(client, token_admin):
    r = client.post(
        "/api/v1/cargas/excel",
        content=b"x",
        headers={
            "Authorization": f"Bearer {token_admin}",
            "Content-Length": str(22 * 1024 * 1024),
        },
    )
    assert r.status_code == 413


def test_layout_legado_ignora_apenas_rodape_conhecido(db_session, tmp_path):
    cab, prod = planilhas(tmp_path)
    linhas = [
        ["Produto: SKU-10U - Produto teste", None, None, None, None, None, None],
        [
            "Data Emissão",
            "Pedido",
            "Cliente",
            "Criador",
            "Preço Líquido (R$)",
            "Quantidade",
            "Subtotal (R$)",
        ],
        ["01/01/2026", "1", "Cliente teste", "Vendedor teste", 10, 2, 20],
        [None, "1", None, None, None, 2, 20],
    ]
    pd.DataFrame(linhas).to_excel(prod, index=False, header=False)
    pedidos = pd.read_excel(cab, dtype=str)
    pedidos.loc[0, "pedido"] = "1"
    pedidos.to_excel(cab, index=False)
    r = ExcelService(db_session).importar_processo_completo(cab, prod)
    assert r["status"] == "sucesso", r
    assert r["itens"] == 1


def test_falha_upload_nao_altera_base_e_registra_historico(
    client, token_admin, tmp_path, db_session
):
    cab, prod = planilhas(tmp_path)
    dados = pd.read_excel(prod)
    dados.loc[0, "quantidade"] = 999
    dados.to_excel(prod, index=False)
    with cab.open("rb") as a, prod.open("rb") as b:
        r = client.post(
            "/api/v1/cargas/excel",
            headers={"Authorization": f"Bearer {token_admin}"},
            files={"arquivo_cabecalho": ("a.xlsx", a), "arquivo_itens": ("b.xlsx", b)},
        )
    assert r.status_code == 422
    assert db_session.query(Venda).count() == db_session.query(Cliente).count() == 0
    from src.backend.app.models import Importacao

    assert db_session.query(Importacao).one().status == "erro"
