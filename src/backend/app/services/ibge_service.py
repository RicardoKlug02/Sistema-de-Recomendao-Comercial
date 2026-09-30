import unicodedata
from typing import Dict, Optional, Tuple
import requests
from time import monotonic


def normalizar_texto(texto: str) -> str:
    if not texto:
        return ""
    nfkd = unicodedata.normalize("NFKD", str(texto))
    sem_acento = "".join([c for c in nfkd if not unicodedata.combining(c)])
    return sem_acento.strip().lower()


class IBGEService:
    _cache_regioes: Dict[Tuple[str, str], str] = {}
    _tentativas: Dict[str, float] = {}

    @classmethod
    def carregar_tabela_municipios(cls, uf: Optional[str] = None):
        """Busca os municípios na API do IBGE (geral ou filtrado por UF) e indexa no cache."""
        url = "https://servicodados.ibge.gov.br/api/v1/localidades/municipios"
        if uf:
            url = f"https://servicodados.ibge.gov.br/api/v1/localidades/estados/{uf.upper()}/municipios"

        try:
            resposta = requests.get(url, timeout=10)
            if resposta.status_code != 200:
                return

            dados = resposta.json()
            for mun in dados:
                nome_mun = normalizar_texto(mun.get("nome", ""))
                
                # Extraindo a UF de forma segura
                imediata = mun.get("regiao-imediata") or {}
                uf_obj = (imediata.get("regiao-intermediaria") or {}).get("UF") or {}
                antiga = ((mun.get("microrregiao") or {}).get("mesorregiao") or {}).get("UF") or {}
                sigla_uf = (uf_obj.get("sigla") or antiga.get("sigla") or "").upper()
                if not sigla_uf and uf:
                    sigla_uf = uf.upper()

                # Nome do polo da região imediata retornado pelo IBGE
                regiao_imediata_obj = mun.get("regiao-imediata") or {}
                nome_polo = regiao_imediata_obj.get("nome", "").strip()

                if nome_mun and sigla_uf and nome_polo:
                    cls._cache_regioes[(nome_mun, sigla_uf)] = nome_polo

        except Exception as e:
            print(f"Aviso: Não foi possível sincronizar com o IBGE: {e}")

    @classmethod
    def obter_regiao_imediata(cls, cidade: str, uf: str = "SC") -> Optional[str]:
        """Recebe o nome da cidade e a UF e devolve o polo regional imediato."""
        cidade_norm = normalizar_texto(cidade)
        uf_norm = uf.strip().upper() if uf else ""
        if not cidade_norm or len(uf_norm) != 2:
            return None

        # Se o cache estiver vazio para esta UF específica, carrega
        if not any(k[1] == uf_norm for k in cls._cache_regioes.keys()) and monotonic() - cls._tentativas.get(uf_norm, float('-inf')) >= 300:
            cls._tentativas[uf_norm] = monotonic()
            cls.carregar_tabela_municipios(uf=uf_norm)

        # 1. Busca exata por (cidade, uf)
        if (cidade_norm, uf_norm) in cls._cache_regioes:
            return cls._cache_regioes[(cidade_norm, uf_norm)]

        return None
