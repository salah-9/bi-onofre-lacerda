"""Utilitários de data e formatação compartilhados entre os dashboards."""

from datetime import datetime
from typing import Optional

FORMATOS = [
    "%d/%m/%Y %H:%M:%S", "%d/%m/%Y %H:%M", "%d/%m/%Y",
    "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d",
]
FORMATOS_SEM_ANO = ["%d/%m %H:%M:%S", "%d/%m %H:%M", "%d/%m"]
HOJE = datetime.today()
_MESES = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]


def inferir_ano(dia: int, mes: int) -> int:
    for ano in (HOJE.year, HOJE.year - 1):
        try:
            if datetime(ano, mes, dia) <= HOJE:
                return ano
        except ValueError:
            pass
    return HOJE.year - 1


def parse_dt(valor) -> Optional[datetime]:
    s = str(valor).strip()
    if not s:
        return None
    for fmt in FORMATOS:
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            pass
    for fmt in FORMATOS_SEM_ANO:
        try:
            dt = datetime.strptime(s, fmt)
            return dt.replace(year=inferir_ano(dt.day, dt.month))
        except ValueError:
            pass
    return None


def trimestre(dt: datetime) -> str:
    return f"{dt.year}-Q{(dt.month - 1) // 3 + 1}"


def mes_ano_key(dt: datetime) -> str:
    return dt.strftime("%Y-%m")


def mes_ano_str(dt: datetime) -> str:
    return f"{_MESES[dt.month - 1]}/{dt.year}"
