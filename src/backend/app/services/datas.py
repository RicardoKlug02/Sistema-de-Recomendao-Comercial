from datetime import datetime
from zoneinfo import ZoneInfo


def hoje_comercial():
    return datetime.now(ZoneInfo("America/Sao_Paulo")).date()
