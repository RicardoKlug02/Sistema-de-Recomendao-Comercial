from datetime import date, timedelta
from types import SimpleNamespace
import pandas as pd
from src.backend.app.services.ritmo_compras import calcular_ritmo
from src.backend.app.services.excel_service import ExcelService
from src.backend.app.services.cliente_service import ClienteService
from src.backend.app.models import Cliente, Venda

REF = date(2026, 9, 29)

def venda(dias, valor):
    return SimpleNamespace(data_venda=REF - timedelta(days=dias), valor_total=valor)

def test_compara_janelas_de_mesmo_tamanho_sem_incluir_o_futuro():
    ritmo = calcular_ritmo([venda(150, 100), venda(119, 300), venda(30, 600),
                            venda(29, 600), venda(0, 1200), venda(-1, 5000)], REF)
    assert ritmo["valor"]["media_habitual"] == 300
    assert ritmo["valor"]["recente"] == 1800
    assert ritmo["valor"]["variacao_pct"] == 500
    assert ritmo["pedidos"]["media_habitual"] == 0.67
    assert ritmo["pedidos"]["recente"] == 2

def test_queda_e_mostrada_sem_classificar_risco():
    ritmo = calcular_ritmo([venda(150, 100), venda(90, 300), venda(60, 300),
                            venda(30, 300), venda(0, 150)], REF)
    assert ritmo["valor"]["variacao_pct"] == -50
    assert ritmo["valor"]["status"] == "COMPARAVEL"

def test_cliente_novo_nao_recebe_variacao_enganosa():
    ritmo = calcular_ritmo([venda(35, 600), venda(5, 100)], REF)
    assert not ritmo["historico_suficiente"]
    assert ritmo["valor"]["variacao_pct"] is None

def test_media_zero_nao_divide_por_zero():
    ritmo = calcular_ritmo([venda(150, 50), venda(90, 0), venda(60, 0), venda(0, 100)], REF)
    assert ritmo["valor"]["variacao_pct"] is None
    assert ritmo["valor"]["status"] == "SEM_BASE_COMPARACAO"

def dados():
    cab = pd.DataFrame([{
        "pedido": str(i), "fabrica": "Fábrica A", "cliente": "Cliente Alfa",
        "cnpj_cpf": "11111111000111", "data": REF - timedelta(days=d), "valor_total": valor,
    } for i, (d, valor) in enumerate([(150, 300), (90, 300), (60, 300), (30, 300), (5, 600)], 1)])
    itens = pd.DataFrame([{
        "pedido": str(i), "sku": "SKU-1", "nome_produto": "Produto Alfa",
        "quantidade": 60 if i == 5 else 30, "preco_unitario": 10,
    } for i in range(2, 6)])
    return cab, itens

def test_dossie_compara_quantidades_e_valores_sem_duplicar_pedido(db_session):
    cab, itens = dados()
    # Dois itens no mesmo pedido não podem duplicar seu valor total.
    itens = pd.concat([itens, itens.iloc[[0]].assign(sku="SKU-2")], ignore_index=True)
    ExcelService(db_session)._validar_e_salvar(cab, itens)
    cid = db_session.query(Cliente).one().id
    ficha = ClienteService(db_session).obter_dossie_cliente(cid, ref_date=REF)
    assert ficha["ritmo_compras"]["valor"]["media_habitual"] == 300
    assert ficha["ritmo_compras"]["valor"]["variacao_pct"] == 100
    p = next(p for p in ficha["comparacao_produtos"] if p["sku"] == "SKU-1")
    assert p["media_habitual"] == 30
    assert p["recente"] == 60
    assert p["variacao_pct"] == 100

def test_pedido_direto_fabrica_conta_no_valor_sem_inventar_quantidades(db_session):
    cab, itens = dados()
    extra = cab.iloc[[0]].assign(pedido="6", data=REF, valor_total=300)
    ExcelService(db_session)._validar_e_salvar(pd.concat([cab, extra], ignore_index=True), itens)
    cid = db_session.query(Cliente).one().id
    ficha = ClienteService(db_session).obter_dossie_cliente(cid, ref_date=REF)
    assert ficha["ritmo_compras"]["valor"]["recente"] == 900
    assert ficha["comparacao_produtos"][0]["status"] == "ITENS_INCOMPLETOS"
    assert ficha["comparacao_produtos"][0]["variacao_pct"] is None

def test_data_iso_de_excel_nao_troca_dia_e_mes(db_session):
    cab, itens = dados()
    cab = cab.iloc[[0]].assign(data="2026-08-01 00:00:00")
    ExcelService(db_session)._validar_e_salvar(cab, itens.iloc[0:0])
    assert db_session.query(Venda).one().data_venda == date(2026, 8, 1)
