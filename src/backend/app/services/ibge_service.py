import unicodedata
from typing import Dict, Optional, Tuple
import requests


def normalizar_texto(texto: str) -> str:
    if not texto:
        return ""
    nfkd = unicodedata.normalize("NFKD", str(texto))
    sem_acento = "".join([c for c in nfkd if not unicodedata.combining(c)])
    return sem_acento.strip().lower()


class IBGEService:
    _cache_regioes: Dict[Tuple[str, str], str] = {}

    @classmethod
    def carregar_tabela_municipios(cls, uf: Optional[str] = None):
        """Busca os municípios na API do IBGE (geral ou filtrado por UF) e indexa no cache."""
        url = "https://servicodados.ibge.gov.br/api/v1/localidades/municipios"
        if uf:
            url = f"https://servicodados.ibge.gov.br/api/v1/localidades/estados/{uf.upper()}/municipios"

        try:
            resposta = requests.get(url, timeout=30)
            if resposta.status_code != 200:
                return

            dados = resposta.json()
            for mun in dados:
                nome_mun = normalizar_texto(mun.get("nome", ""))
                
                # Extraindo a UF de forma segura
                sigla_uf = (
                    mun.get("microrregiao", {})
                    .get("mesorregiao", {})
                    .get("UF", {})
                    .get("sigla", "")
                    .upper()
                )
                if not sigla_uf and uf:
                    sigla_uf = uf.upper()

                # Nome do polo da região imediata retornado pelo IBGE
                regiao_imediata_obj = mun.get("regiao-imediata", {})
                nome_polo = regiao_imediata_obj.get("nome", "").strip()

                if nome_mun and sigla_uf:
                    cls._cache_regioes[(nome_mun, sigla_uf)] = nome_polo or mun.get("nome")

        except Exception as e:
            print(f"Aviso: Não foi possível sincronizar com o IBGE: {e}")

    @classmethod
    def obter_regiao_imediata(cls, cidade: str, uf: str = "SC") -> Optional[str]:
        """Recebe o nome da cidade e a UF e devolve o polo regional imediato."""
        cidade_norm = normalizar_texto(cidade)
        uf_norm = uf.strip().upper() if uf else "SC"

        # Se o cache estiver vazio para esta UF específica, carrega
        if not any(k[1] == uf_norm for k in cls._cache_regioes.keys()):
            cls.carregar_tabela_municipios(uf=uf_norm)

        # 1. Busca exata por (cidade, uf)
        if (cidade_norm, uf_norm) in cls._cache_regioes:
            return cls._cache_regioes[(cidade_norm, uf_norm)]

        # 2. Fallback: busca apenas pelo nome do município independente da UF
        for (mun, _), regiao in cls._cache_regioes.items():
            if mun == cidade_norm:
                return regiao

        return cidade.strip().title() if cidade else None