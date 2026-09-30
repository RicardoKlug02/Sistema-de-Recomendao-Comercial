from unittest.mock import Mock
from src.backend.app.services.ibge_service import IBGEService


def test_regiao_por_cidade_uf_sem_confundir_homonimos(monkeypatch):
    monkeypatch.setattr(IBGEService, "_cache_regioes", {})
    monkeypatch.setattr(IBGEService, "_tentativas", {})
    resposta = Mock(status_code=200)
    resposta.json.return_value = [{"nome": "Indaial", "microrregiao": None,
        "regiao-imediata": {"nome": "Blumenau", "regiao-intermediaria": {"UF": {"sigla": "SC"}}}}]
    buscar = Mock(return_value=resposta)
    monkeypatch.setattr("src.backend.app.services.ibge_service.requests.get", buscar)
    assert IBGEService.obter_regiao_imediata("INDAIAL", "SC") == "Blumenau"
    assert IBGEService.obter_regiao_imediata("Indaial", "SC") == "Blumenau"
    assert buscar.call_count == 1
    resposta.json.return_value = []
    assert IBGEService.obter_regiao_imediata("Indaial", "PR") is None


def test_falha_ibge_nao_repete_consulta_por_cliente(monkeypatch):
    monkeypatch.setattr(IBGEService, "_cache_regioes", {})
    monkeypatch.setattr(IBGEService, "_tentativas", {})
    buscar = Mock(side_effect=TimeoutError("IBGE indisponível"))
    monkeypatch.setattr("src.backend.app.services.ibge_service.requests.get", buscar)
    assert IBGEService.obter_regiao_imediata("Indaial", "SC") is None
    assert IBGEService.obter_regiao_imediata("Blumenau", "SC") is None
    assert buscar.call_count == 1
