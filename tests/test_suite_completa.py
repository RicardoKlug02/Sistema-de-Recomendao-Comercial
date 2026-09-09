import sys
from pathlib import Path

raiz = Path(__file__).resolve().parent.parent
if str(raiz) not in sys.path:
    sys.path.insert(0, str(raiz))

import pytest
from sqlalchemy.orm import Session
from src.backend.app.core.database import engine
from src.backend.app.core.security import decrypt_data, encrypt_data
from src.backend.app.models.cliente import Cliente
from src.backend.app.models.item_venda import ItemVenda
from src.backend.app.models.produto import Produto
from src.backend.app.services.associacao_service import AssociacaoService
from src.backend.app.services.colaborativo_service import ColaborativoService
from src.backend.app.services.excel_service import normalizar_sku
from src.backend.app.services.recompra_service import RecompraService
from src.backend.app.services.recomendacao_service import RecomendacaoService


@pytest.fixture(scope="module")
def db():
    """Sessão com o banco de dados."""
    with Session(engine) as session:
        yield session


# =====================================================================
# 1. SEGURANÇA E LGPD
# =====================================================================
def test_criptografia_e_decriptografia_reversivel():
    dado_original = "Empresa Teste Parafusos e Ferramentas LTDA"
    cifrado = encrypt_data(dado_original)

    assert cifrado != dado_original, "O dado não foi cifrado!"
    assert isinstance(cifrado, str)

    decriptado = decrypt_data(cifrado)
    assert decriptado == dado_original, "A decriptografia falhou em restaurar o texto original!"


def test_decriptografia_valores_vazios():
    assert decrypt_data("") == ""
    assert decrypt_data(None) is None


# =====================================================================
# 2. ENGENHARIA DE DADOS & NORMALIZAÇÃO DE SKU
# =====================================================================
@pytest.mark.parametrize(
    "sku_entrada, sku_esperado",
    [
        ("39189U", "39189"),
        ("31926u", "31926"),
        ("10293-U", "10293-"),
        ("5.50.10.SI", "5.50.10.SI"),
        ("PARAFUSO", "PARAFUSO"),
        ("", ""),
    ],
)
def test_regras_normalizacao_sku(sku_entrada, sku_esperado):
    assert normalizar_sku(sku_entrada) == sku_esperado


# =====================================================================
# 3. SERVIÇO DE RECOMPRA & CHURN
# =====================================================================
def test_recompra_analisar_oportunidades(db):
    service = RecompraService(db_session=db)
    cliente = db.query(Cliente).first()
    if not cliente:
        pytest.skip("Banco sem clientes cadastrados.")

    oportunidades = service.analisar_oportunidades_cliente(cliente_id=cliente.id)
    assert isinstance(oportunidades, list)

    for op in oportunidades:
        assert "produto_id" in op
        assert "sku" in op
        assert "periodicidade_media_dias" in op
        assert "dias_atraso" in op
        assert "status" in op
        assert op["dias_atraso"] >= 0


def test_recompra_alertas_globais_home(db):
    service = RecompraService(db_session=db)
    alertas = service.obter_alertas_globais_alto_volume(percentil_volume=0.3, limite_alertas=5)
    assert isinstance(alertas, list)

    for al in alertas:
        assert "cliente_id" in al
        assert "sku" in al
        assert "volume_medio_pedido" in al
        assert "dias_atraso" in al
        assert al["dias_atraso"] > 0


# =====================================================================
# 4. SERVIÇO COLABORATIVO (EXPANSÃO DE MIX)
# =====================================================================
def test_colaborativo_encontrar_grupos_similares(db):
    service = ColaborativoService(db_session=db)
    cliente = db.query(Cliente).first()
    if not cliente:
        pytest.skip("Banco sem clientes cadastrados.")

    grupos = service.encontrar_grupos_similares(cliente_id=cliente.id, top_k=3)
    assert isinstance(grupos, list)

    for g in grupos:
        assert "grupo_economico" in g
        assert "similaridade" in g
        assert 0.0 <= g["similaridade"] <= 100.0


def test_colaborativo_recomendar_produtos(db):
    service = ColaborativoService(db_session=db)
    cliente = db.query(Cliente).first()
    if not cliente:
        pytest.skip("Banco sem clientes cadastrados.")

    recoms = service.recomendar_produtos_cliente(cliente_id=cliente.id, top_n_produtos=4)
    assert isinstance(recoms, list)

    for r in recoms:
        assert "produto_id" in r
        assert "sku" in r
        assert "afinidade_percentual" in r
        assert "volume_sugerido_unidades" in r
        assert 0.0 <= r["afinidade_percentual"] <= 100.0


# =====================================================================
# 5. SERVIÇO DE ASSOCIAÇÃO (CROSS-SELLING)
# =====================================================================
def test_associacao_recomendar_cross_selling(db):
    service = AssociacaoService(db_session=db)
    produtos = db.query(ItemVenda.produto_id).distinct().limit(2).all()
    if not produtos:
        pytest.skip("Banco sem itens de venda cadastrados.")

    p_ids = [p[0] for p in produtos]
    cross = service.recomendar_cross_selling(
        produto_ids=p_ids, min_support=0.001, min_confidence=0.1
    )
    assert isinstance(cross, list)

    for c in cross:
        assert "produto_id" in c
        assert "confianca_pct" in c
        assert "lift" in c
        assert c["produto_id"] not in p_ids


# =====================================================================
# 6. FACHADA ORQUESTRADORA (RECOMENDACAO SERVICE)
# =====================================================================
def test_fachada_painel_visao_360(db):
    service = RecomendacaoService(db_session=db)
    cliente = db.query(Cliente).first()
    if not cliente:
        pytest.skip("Banco sem clientes cadastrados.")

    painel = service.obter_painel_visao_360(cliente_id=cliente.id)

    assert isinstance(painel, dict)
    assert painel["cliente_id"] == cliente.id
    assert "razao_social" in painel
    assert "alertas_recompra" in painel
    assert "expansao_mix" in painel
    assert "ultimos_pedidos" in painel

    # Garante que o texto descriptografado não vazou formato Fernet em Base64
    if cliente.razao_social:
        assert not painel["razao_social"].startswith("gAAAAA")


def test_fachada_alertas_home_descriptografados(db):
    service = RecomendacaoService(db_session=db)
    alertas = service.obter_alertas_home(limite=5)
    assert isinstance(alertas, list)

    for al in alertas:
        if "razao_social" in al:
            assert not al["razao_social"].startswith("gAAAAA")