from datetime import date
import io
import pandas as pd
import pytest
from src.backend.app.models import Cliente, Fabrica, ItemVenda, Produto, Venda
from src.backend.app.services.excel_service import ExcelService
from src.backend.app.services.cliente_service import ClienteService
from src.backend.app.services.comercial_service import ComercialService
from src.backend.app.services.associacao_service import AssociacaoService


@pytest.fixture(autouse=True)
def ibge_sem_rede(monkeypatch):
    from src.backend.app.services.ibge_service import IBGEService
    monkeypatch.setattr(IBGEService, "obter_regiao_imediata", lambda cidade, uf: "Blumenau" if uf == "SC" else None)


def cabecalhos():
    return pd.DataFrame([
        {"pedido": "1", "fabrica": "Fábrica A", "cliente": "Cliente Alfa", "cnpj_cpf": "11111111000111",
         "data": "01/08/2026", "valor_total": 100, "cidade": "Indaial", "estado": "SC", "vendedor": "Ana", "rede": "Rede Alfa"},
        {"pedido": "2", "fabrica": "Fábrica B", "cliente": "Cliente Alfa", "cnpj_cpf": "11111111000111",
         "data": "15/08/2026", "valor_total": 200, "cidade": "Indaial", "estado": "SC", "vendedor": "Ana", "rede": "Rede Alfa"},
    ])


def itens():
    return pd.DataFrame([{"pedido": "1", "sku": "SKU-1", "nome_produto": "Produto Alfa",
                          "quantidade": 10, "preco_unitario": 10}])


def test_pedido_direto_fabrica_conta_em_indicadores_e_dossie(db_session):
    ExcelService(db_session)._validar_e_salvar(cabecalhos(), itens())
    painel = ComercialService(db_session).painel("2026-08")["indicadores"]
    assert painel["venda_total"] == 300
    assert painel["pedidos_emitidos"] == 2
    assert painel["ticket_medio"] == 150
    assert painel["pedidos_sem_itens"] == 1
    assert db_session.query(Fabrica).count() == 2
    cliente = db_session.query(Cliente).one()
    assert (cliente.cidade, cliente.estado) == ("Indaial", "SC")
    ficha = ClienteService(db_session).obter_dossie_cliente(cliente.id, ref_date=date(2026, 9, 29))
    assert ficha["valor_comprado"] == 300
    assert ficha["pedidos_emitidos"] == 2
    assert len(ficha["resumo_fabricas"]) == 2
    assert len(ComercialService(db_session).painel("2026-08")["produtos"]) == 1


def test_reimportacao_e_idempotente_e_sem_itens_nao_apaga(db_session):
    service = ExcelService(db_session)
    service._validar_e_salvar(cabecalhos(), itens())
    service._validar_e_salvar(cabecalhos(), itens())
    assert db_session.query(Venda).count() == 2
    assert db_session.query(ItemVenda).count() == 1
    service._validar_e_salvar(cabecalhos(), itens().iloc[0:0])
    assert db_session.query(ItemVenda).count() == 1


def test_numero_pedido_e_sku_podem_repetir_em_fabricas_distintas(db_session):
    cab = cabecalhos()
    cab["pedido"] = "1"
    prod = pd.concat([itens().assign(fabrica="Fábrica A"), itens().assign(fabrica="Fábrica B")])
    ExcelService(db_session)._validar_e_salvar(cab, prod)
    assert db_session.query(Venda).count() == 2
    assert db_session.query(Produto).count() == 2
    assert db_session.query(ItemVenda).count() == 2


def test_ambiguidade_de_fabrica_rejeita_sem_gravar(db_session):
    cab = cabecalhos()
    cab["pedido"] = "1"
    with pytest.raises(ValueError, match="número repetido"):
        ExcelService(db_session)._validar_e_salvar(cab, itens())
    assert db_session.query(Venda).count() == 0


def test_data_invalida_nao_vira_compra_recente(db_session):
    cab = cabecalhos()
    cab.loc[1, "data"] = "data inválida"
    with pytest.raises(ValueError, match="data inválida"):
        ExcelService(db_session)._validar_e_salvar(cab, itens())
    assert db_session.query(Venda).count() == 0


def test_itens_orfaos_sao_contabilizados_em_aviso(db_session):
    prod = pd.concat([itens(), itens().assign(pedido="999")])
    result = ExcelService(db_session)._validar_e_salvar(cabecalhos(), prod)
    assert result["itens_ignorados"] == 1
    assert result["itens"] == 1
    assert any("sem cabeçalho" in aviso for aviso in result["avisos"])


def test_busca_nome_cobre_cliente_apos_primeiros_300(db_session):
    db_session.add_all([Cliente(razao_social=f"Cliente {i}") for i in range(300)])
    alvo = Cliente(razao_social="Distribuidora Única")
    db_session.add(alvo)
    db_session.commit()
    assert ClienteService(db_session).buscar_por_termo("unica")[0]["id"] == alvo.id


def test_dossie_agrupa_rede_incluindo_pedidos_sem_itens(db_session):
    service = ExcelService(db_session)
    cab = cabecalhos()
    cab.loc[1, "cnpj_cpf"] = "22222222000122"
    cab.loc[1, "cliente"] = "Filial Beta"
    service._validar_e_salvar(cab, itens())
    cid = db_session.query(Cliente).order_by(Cliente.id).first().id
    assert ClienteService(db_session).obter_dossie_cliente(cid)["valor_comprado"] == 100
    rede = ClienteService(db_session).obter_dossie_cliente(cid, agrupar_rede=True)
    assert rede["valor_comprado"] == 300
    assert rede["clientes_agrupados"] == 2


def xlsx(df):
    arquivo = io.BytesIO()
    df.to_excel(arquivo, index=False)
    return arquivo.getvalue()


def test_fluxo_api_carga_painel_cliente_alertas(client, token_admin):
    headers = {"Authorization": f"Bearer {token_admin}"}
    arquivos = {
        "arquivo_cabecalho": ("pedidos.xlsx", xlsx(cabecalhos())),
        "arquivo_itens": ("itens.xlsx", xlsx(itens())),
    }
    previa = client.post("/api/v1/cargas/conferir", headers=headers, files=arquivos)
    assert previa.status_code == 200, previa.text
    assert client.get("/api/v1/cargas/historico", headers=headers).json() == []
    resposta = client.post("/api/v1/cargas/excel", headers=headers, files=arquivos,
                          data={"token_conferencia": previa.json()["token_conferencia"], "vendas_comissao": "true"})
    assert resposta.status_code == 200, resposta.text
    assert resposta.json()["pedidos_sem_itens"] == 1
    painel = client.get("/api/v1/comercial/painel?mes=2026-08", headers=headers)
    assert painel.status_code == 200
    assert painel.json()["indicadores"]["venda_total"] == 300
    cid = painel.json()["clientes"][0]["id"]
    ficha = client.get(f"/api/v1/clientes/{cid}", headers=headers)
    assert ficha.status_code == 200
    assert len(ficha.json()["resumo_fabricas"]) == 2
    assert client.get("/api/v1/comercial/alertas", headers=headers).status_code == 200
    historico = client.get("/api/v1/cargas/historico", headers=headers).json()
    assert len(historico) == 1
    assert historico[0]["processados"] == 2


def test_conferencia_nao_grava_e_nao_aceita_arquivos_alterados(client, token_admin, db_session):
    headers = {"Authorization": f"Bearer {token_admin}"}
    arquivos = {"arquivo_cabecalho": ("pedidos.xlsx", xlsx(cabecalhos())), "arquivo_itens": ("itens.xlsx", xlsx(itens()))}
    previa = client.post("/api/v1/cargas/conferir", headers=headers, files=arquivos)
    assert previa.status_code == 200, previa.text
    assert db_session.query(Venda).count() == db_session.query(Cliente).count() == db_session.query(Fabrica).count() == 0
    dados = {"token_conferencia": previa.json()["token_conferencia"], "vendas_comissao": "true"}
    modificados = {**arquivos, "arquivo_itens": ("itens.xlsx", xlsx(itens().assign(quantidade=20)))}
    assert client.post("/api/v1/cargas/excel", headers=headers, files=modificados, data=dados).status_code == 409
    assert db_session.query(Venda).count() == 0
    assert client.post("/api/v1/cargas/excel", headers=headers, files=arquivos, data={**dados, "vendas_comissao": "false"}).status_code == 422
    assert client.post("/api/v1/cargas/excel", headers=headers, files=arquivos, data=dados).status_code == 200
    assert client.post("/api/v1/cargas/excel", headers=headers, files=arquivos, data=dados).status_code == 409


def test_somente_tipo_venda_e_aceito(db_session):
    with pytest.raises(ValueError, match="somente pedidos"):
        ExcelService(db_session)._validar_e_salvar(cabecalhos().assign(tipo_pedido="Bonificação"), itens())
    assert db_session.query(Venda).count() == 0
    ExcelService(db_session)._validar_e_salvar(cabecalhos().assign(tipo_pedido="Venda"), itens())


def test_abertura_fabrica_diferente_de_cliente_novo(db_session):
    service = ExcelService(db_session)
    cab = cabecalhos()
    cab.loc[0, "data"] = "01/07/2026"
    cab.loc[1, "vendedor"] = "Bruno"
    recompra = cab.iloc[[1]].assign(pedido="3", data="20/08/2026")
    service._validar_e_salvar(pd.concat([cab, recompra], ignore_index=True), itens())
    painel = ComercialService(db_session).painel("2026-08")
    assert painel["indicadores"]["clientes_novos"] == 0
    assert painel["indicadores"]["aberturas_cliente_fabrica"] == 1
    assert painel["aberturas"][0]["novo_no_escritorio"] is False
    assert painel["regioes"] == [{"nome": "Blumenau", "uf": "SC", "valor": 400}]
    from src.backend.app.models import Vendedor
    ana = db_session.query(Vendedor).filter_by(nome="Ana").one()
    assert ComercialService(db_session).painel("2026-08", ana.id)["indicadores"]["aberturas_cliente_fabrica"] == 0


def test_rotas_operacionais_exigem_login(client):
    for rota in ("/comercial/painel", "/comercial/clientes", "/comercial/alertas", "/auth/usuarios", "/cargas/historico"):
        assert client.get("/api/v1" + rota).status_code == 401

def test_mes_e_vendedor_nao_incluem_vendas_de_outro_periodo(db_session):
    cab = cabecalhos()
    cab.loc[1, "vendedor"] = "Bruno"
    outro = cab.iloc[[0]].copy()
    outro["pedido"] = "3"
    outro["data"] = "01/09/2026"
    outro["valor_total"] = 500
    ExcelService(db_session)._validar_e_salvar(pd.concat([cab, outro], ignore_index=True), itens())
    from src.backend.app.models import Vendedor
    ana = db_session.query(Vendedor).filter_by(nome="Ana").one()
    painel = ComercialService(db_session).painel("2026-08", ana.id)
    assert painel["indicadores"]["venda_total"] == 100
    assert painel["indicadores"]["pedidos_emitidos"] == 1
    assert painel["indicadores"]["clientes_novos"] == 1
    assert painel["faturamento_mensal"][-1]["valor"] == 100
    assert ComercialService(db_session).painel("2026-09")["indicadores"]["venda_total"] == 500


def test_valor_em_branco_rejeita_carga(db_session):
    cab = cabecalhos()
    cab.loc[1, "valor_total"] = None
    with pytest.raises(ValueError, match="obrigatório"):
        ExcelService(db_session)._validar_e_salvar(cab, itens())
    assert db_session.query(Venda).count() == 0


def test_recompra_individual_usa_id_em_vez_de_comparar_texto_criptografado(db_session):
    cab = cabecalhos()
    cab["fabrica"] = "Fábrica A"
    cab["rede"] = None
    produtos = pd.concat([itens(), itens().assign(pedido="2")], ignore_index=True)
    ExcelService(db_session)._validar_e_salvar(cab, produtos)
    from src.backend.app.services.recompra_service import RecompraService
    cid = db_session.query(Cliente).one().id
    oportunidades = RecompraService(db_session).analisar_oportunidades_cliente(cid, ref_date=date(2026, 9, 29))
    assert len(oportunidades) == 1
    assert oportunidades[0]["periodicidade_media_dias"] == 14


def test_pedido_de_um_unico_produto_entra_no_denominador_de_associacao(db_session):
    cab = pd.concat([cabecalhos().iloc[[0]].assign(pedido=str(i)) for i in range(1, 6)], ignore_index=True)
    produtos = pd.concat([
        itens(), itens().assign(sku="SKU-2"),
        itens().assign(pedido="2"), itens().assign(pedido="2", sku="SKU-2"),
        itens().assign(pedido="3"),
        itens().assign(pedido="4", sku="SKU-3"), itens().assign(pedido="5", sku="SKU-3"),
    ], ignore_index=True)
    ExcelService(db_session)._validar_e_salvar(cab, produtos)
    alvo = db_session.query(Produto).filter_by(sku="SKU-1").one()
    regras = AssociacaoService(db_session).recomendar_cross_selling([alvo.id])
    assert len(regras) == 1
    assert regras[0]["sku"] == "SKU-2"
    assert regras[0]["confianca_pct"] == 66.7
    assert regras[0]["lift"] == 1.67

def test_colunas_do_relatorio_erp_sao_reconhecidas(db_session, tmp_path):
    arquivo = tmp_path / "pedidos.xlsx"
    pd.DataFrame([{
        "Data de emissão": "01/08/2026", "Pedido": "1", "Representada": "Fábrica A",
        "Razão Social": "Cliente Alfa", "CNPJ/CPF": "11111111000111",
        "Total em produtos": "R$ 100,00", "Rede de clientes": "Rede Alfa", "Vendedor(a)": "Ana",
    }]).to_excel(arquivo, index=False)
    service = ExcelService(db_session)
    cab = service._limpar_excel_cabecalho(arquivo)
    assert cab.loc[0, "valor_total"] == 100
    assert cab.loc[0, "rede"] == "Rede Alfa"
    assert cab.loc[0, "vendedor"] == "Ana"
    service._validar_e_salvar(cab, itens())
    assert db_session.query(Cliente).one().grupo_economico == "Rede Alfa"


def test_layout_erp_com_cabecalho_na_linha_11(db_session, tmp_path):
    arquivo = tmp_path / "relatorio.xlsx"
    dados = pd.DataFrame([{"Data de emissão": "29/09/2026", "Pedido": "36834", "Representada": "BIANPLAST",
                          "Razão Social": "Cliente exemplo", "Nome Fantasia": "Loja exemplo",
                          "CNPJ/CPF": "07295822000781", "Cidade": "CURITIBA", "Estado": "PR",
                          "Rede de clientes": "Rede exemplo", "Vendedor(a)": "Sergio",
                          "Tipo do pedido": "Venda", "Total em produtos": "4.349,00"}])
    with pd.ExcelWriter(arquivo) as writer:
        pd.DataFrame([['Relatório de vendas'], ['Filtros'], ['Tipo de pedido: Venda'],
                      ['Situação dos pedidos: Pedidos concluídos']]).to_excel(writer, index=False, header=False)
        dados.to_excel(writer, index=False, startrow=10)
    service = ExcelService(db_session)
    cab = service._limpar_excel_cabecalho(arquivo)
    previa = service.conferir(cab, itens().iloc[:0])
    assert cab.loc[0, "cnpj_cpf"] == "07295822000781"
    assert cab.loc[0, "tipo_pedido"] == "Venda"
    assert previa["valor_total"] == 4349
    assert previa["pedidos_sem_itens"] == 1
    assert db_session.query(Venda).count() == 0


def test_totalizador_do_relatorio_produtos_nao_vira_item(db_session, tmp_path):
    arquivo = tmp_path / "itens.xlsx"
    pd.DataFrame([
        ["Produto: 1024U - Produto Alfa", None, None, None, None, None, None],
        ["Data Emissão", "Pedido", "Cliente", "Criador", "Preço Líquido (R$)", "Quantidade", "Subtotal (R$)"],
        ["01/08/2026", "1", "Cliente Alfa", "Ana", "10", "10", "100"],
        [None, "1", None, None, None, "10", "100"],
    ]).to_excel(arquivo, header=False, index=False)
    prod = ExcelService(db_session)._limpar_excel_produtos(arquivo)
    assert len(prod) == 1
    assert prod.iloc[0]["sku"] == "1024"
    assert prod.iloc[0]["quantidade"] == 10
