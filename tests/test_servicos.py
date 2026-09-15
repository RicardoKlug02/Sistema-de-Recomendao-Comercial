from datetime import date
from dateutil.relativedelta import relativedelta
from src.backend.app.models.cliente import Cliente
from src.backend.app.models.fabrica import Fabrica
from src.backend.app.models.produto import Produto
from src.backend.app.models.venda import Venda
from src.backend.app.models.item_venda import ItemVenda
from src.backend.app.services.excel_service import ExcelService
from src.backend.app.services.cliente_service import ClienteService
from src.backend.app.services.recompra_service import RecompraService
from src.backend.app.core.security import gerar_blind_index


def test_excel_service_normalizacao_e_conversoes(db_session):
    service = ExcelService(db_session=db_session)
    assert service.normalizar_sku("1024U") == "1024"
    assert service.normalizar_sku("1024u") == "1024"
    assert service.normalizar_sku("SKU-99") == "SKU-99"
    assert service._converter_valor_br("R$ 1.250,50") == 1250.50
    assert service._converter_valor_br("450,00") == 450.00
    assert service._converter_valor_br(None) == 0.0


def test_busca_hibrida_cliente_service(db_session):
    doc_real = "11.222.333/0001-44"
    doc_hash = gerar_blind_index(doc_real)

    cliente = Cliente(
        razao_social="Distribuidora Catarinense de Bebidas",
        nome_fantasia="Adega Vale",
        cnpj_cpf="CLI_ANON_123",
        cnpj_hash=doc_hash,
        grupo_economico="GRUPO_ADEGA",
        cidade="Pomerode",
        estado="SC",
    )
    db_session.add(cliente)
    db_session.commit()

    service = ClienteService(db_session=db_session)

    # 1. Busca exata por Blind Index (via documento digitado)
    busca_doc = service.buscar_por_termo("11222333000144")
    assert len(busca_doc) == 1
    assert busca_doc[0]["razao_social"] == "Distribuidora Catarinense de Bebidas"

    # 2. Busca por Grupo Econômico
    busca_grupo = service.buscar_por_termo("ADEGA")
    assert len(busca_grupo) == 1

    # 3. Busca decifrada em memória por Razão Social parcial
    busca_nome = service.buscar_por_termo("Catarinense")
    assert len(busca_nome) == 1
    assert busca_nome[0]["cidade"] == "Pomerode"


def test_dossie_e_alertas_de_churn_recompra(db_session):
    hoje = date(2026, 9, 14)
    
    fabrica = Fabrica(nome_fantasia="Argaplan Indústria")
    cliente = Cliente(
        razao_social="Cliente Teste Alerta",
        cnpj_cpf="CLI_0001",
        cnpj_hash="hash_0001"
    )
    # Cliente secundário para definir a régua da média do banco
    cliente_padrao = Cliente(
        razao_social="Cliente Varejo Baixo Volume",
        cnpj_cpf="CLI_0002",
        cnpj_hash="hash_0002"
    )
    db_session.add_all([fabrica, cliente, cliente_padrao])
    db_session.flush()

    produto = Produto(sku="ARG-10", nome="Argamassa ACIII", fabrica_id=fabrica.id)
    db_session.add(produto)
    db_session.flush()

    # Venda base de baixo volume (para a média geral ser baixa)
    venda_base = Venda(
        numero_pedido="PED-BASE",
        cliente_id=cliente_padrao.id,
        fabrica_id=fabrica.id,
        data_venda=hoje - relativedelta(days=200),
        valor_total=200.0,
    )
    db_session.add(venda_base)
    db_session.flush()
    db_session.add(ItemVenda(venda_id=venda_base.id, produto_id=produto.id, quantidade=5, preco_unitario=40.0))

    # Vendas do Cliente de Alto Volume (volume 100 > corte de 1.2x da média)
    venda_1 = Venda(
        numero_pedido="PED-1",
        cliente_id=cliente.id,
        fabrica_id=fabrica.id,
        data_venda=hoje - relativedelta(days=150),
        valor_total=10000.0,
    )
    venda_2 = Venda(
        numero_pedido="PED-2",
        cliente_id=cliente.id,
        fabrica_id=fabrica.id,
        data_venda=hoje - relativedelta(days=100),
        valor_total=9000.0,
    )
    db_session.add_all([venda_1, venda_2])
    db_session.flush()

    item_1 = ItemVenda(venda_id=venda_1.id, produto_id=produto.id, quantidade=100, preco_unitario=100.0)
    item_2 = ItemVenda(venda_id=venda_2.id, produto_id=produto.id, quantidade=100, preco_unitario=90.0)
    db_session.add_all([item_1, item_2])
    db_session.commit()

    # 1. Teste do Dossiê 360
    service_cliente = ClienteService(db_session=db_session)
    dossie = service_cliente.obter_dossie_cliente(cliente.id, ref_date=hoje)

    assert len(dossie["resumo_fabricas"]) == 1
    assert dossie["resumo_fabricas"][0]["status"] == "Inativo na Fábrica"
    assert dossie["resumo_fabricas"][0]["dias_sem_comprar"] == 100

    # 2. Teste de Alertas Globais de Alto Volume
    service_recompra = RecompraService(db_session=db_session)
    alertas = service_recompra.obter_alertas_globais_alto_volume(ref_date=hoje)
    assert len(alertas) >= 1
    assert alertas[0]["cliente_id"] == cliente.id
    assert alertas[0]["sku"] == "ARG-10"