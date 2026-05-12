#!/usr/bin/env python3
"""Relatório de SLA de atendimento por corretor.

SLA = tempo entre criação do lead e primeiro contato realizado.

Uso:
    python3 scripts/relatorio_sla.py              # todos os períodos
    python3 scripts/relatorio_sla.py 2025-Q3      # trimestre específico
    python3 scripts/relatorio_sla.py --amostrar   # mostra 5 linhas brutas para debug
"""

import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

import gspread

ROOT = Path(__file__).parent.parent
CLIENT_SECRET = ROOT / "client_secret.json"
TOKEN_DIR = ROOT / ".auth"
SPREADSHEET_ID = "1yPE_XlMWbk1di6xK2bD68w5IbZkVi2JqILC0bXwEykc"

GREEN  = "\033[32m"
YELLOW = "\033[33m"
RED    = "\033[31m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

# Metas de SLA
META_VERDE    = 2    # horas — excelente
META_AMARELO  = 24   # horas — aceitável


def autenticar() -> gspread.Client:
    return gspread.oauth(
        credentials_filename=str(CLIENT_SECRET),
        authorized_user_filename=str(TOKEN_DIR / "token.json"),
    )


FORMATOS_COM_ANO = [
    "%d/%m/%Y %H:%M:%S",
    "%d/%m/%Y %H:%M",
    "%d/%m/%Y",
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%d",
]

FORMATOS_SEM_ANO = [
    "%d/%m %H:%M:%S",
    "%d/%m %H:%M",
    "%d/%m",
]

HOJE = datetime.today()


def inferir_ano(dia: int, mes: int) -> int:
    """Atribui o ano mais recente que não coloque a data no futuro."""
    for ano in (HOJE.year, HOJE.year - 1):
        try:
            dt = datetime(ano, mes, dia)
            if dt <= HOJE:
                return ano
        except ValueError:
            pass
    return HOJE.year - 1


def parse_dt(valor: str) -> Optional[datetime]:
    valor = str(valor).strip()
    if not valor:
        return None
    for fmt in FORMATOS_COM_ANO:
        try:
            return datetime.strptime(valor, fmt)
        except ValueError:
            continue
    for fmt in FORMATOS_SEM_ANO:
        try:
            dt = datetime.strptime(valor, fmt)
            ano = inferir_ano(dt.day, dt.month)
            return dt.replace(year=ano)
        except ValueError:
            continue
    return None


def trimestre_de_dt(dt: datetime) -> str:
    return f"{dt.year}-Q{(dt.month - 1) // 3 + 1}"


def cor_sla(horas: float) -> str:
    if horas <= META_VERDE:
        return GREEN
    if horas <= META_AMARELO:
        return YELLOW
    return RED


def fmt_duracao(horas: float) -> str:
    if horas < 1:
        return f"{int(horas * 60)}min"
    if horas < 24:
        return f"{horas:.1f}h"
    dias = int(horas // 24)
    resto = horas % 24
    return f"{dias}d {resto:.0f}h"


def carregar_leads(gc: gspread.Client) -> list[dict]:
    sh = gc.open_by_key(SPREADSHEET_ID)
    ws = sh.worksheet("LeadsConsolidados")
    return ws.get_all_records()


def amostrar(gc: gspread.Client) -> None:
    registros = carregar_leads(gc)
    print(f"Total de linhas: {len(registros)}")
    print(f"Cabeçalhos: {list(registros[0].keys())}\n")
    for row in registros[:5]:
        print(row)


def calcular_sla(gc: gspread.Client, filtro_trimestre: Optional[str]) -> None:
    registros = carregar_leads(gc)
    print(f"  LeadsConsolidados: {len(registros)} registros\n")

    # Agrupa por corretor: lista de horas de SLA válidas
    por_corretor: dict[str, list[float]] = {}
    sem_contato = sem_data = 0

    for row in registros:
        criado_raw   = row.get("Data Criaçao Oportunidade") or row.get("Data Criação Lead", "")
        contato_raw  = row.get("Data Primeiro Contato", "")
        corretor     = str(row.get("Responsável", "")).strip()

        if not corretor:
            continue

        dt_criado  = parse_dt(criado_raw)
        dt_contato = parse_dt(contato_raw)

        if dt_criado is None:
            sem_data += 1
            continue

        # Filtra por trimestre se informado
        if filtro_trimestre and trimestre_de_dt(dt_criado) != filtro_trimestre:
            continue

        if dt_contato is None:
            sem_contato += 1
            por_corretor.setdefault(corretor, [])  # garante que aparece no ranking
            continue

        if dt_contato < dt_criado:
            # Data inconsistente — ignora
            continue

        horas = (dt_contato - dt_criado).total_seconds() / 3600
        por_corretor.setdefault(corretor, []).append(horas)

    if sem_data:
        print(f"  ⚠ {sem_data} registros sem data de criação — ignorados")
    if sem_contato:
        print(f"  ⚠ {sem_contato} leads sem data de primeiro contato (em aberto ou não contatados)\n")

    if not por_corretor:
        print("Nenhum dado encontrado para o período informado.")
        return

    # Calcula médias e ordena do mais rápido para o mais lento
    resumo = []
    for corretor, tempos in por_corretor.items():
        if tempos:
            media = sum(tempos) / len(tempos)
            minimo = min(tempos)
            maximo = max(tempos)
        else:
            media = minimo = maximo = None
        resumo.append((corretor, len(tempos), media, minimo, maximo))

    # Ordena: corretores com média primeiro (mais rápidos), sem dados no fim
    resumo.sort(key=lambda x: (x[2] is None, x[2] or 0))

    col = max(len(r[0]) for r in resumo) + 2
    titulo = f"SLA de Atendimento" + (f" — {filtro_trimestre}" if filtro_trimestre else " — Todos os períodos")

    print(f"{BOLD}{'─' * 72}{RESET}")
    print(f"{BOLD}  {titulo}{RESET}")
    print(f"  Verde ≤ {META_VERDE}h  |  Amarelo ≤ {META_AMARELO}h  |  Vermelho > {META_AMARELO}h")
    print(f"{'─' * 72}")
    print(f"  {'Corretor':<{col}} {'Contatos':>8} {'Média':>10} {'Mínimo':>10} {'Máximo':>10}")
    print(f"{'─' * 72}")

    for corretor, n_contatos, media, minimo, maximo in resumo:
        if media is not None:
            cor = cor_sla(media)
            print(
                f"  {cor}{corretor:<{col}}{RESET}"
                f" {n_contatos:>8}"
                f" {cor}{fmt_duracao(media):>10}{RESET}"
                f" {fmt_duracao(minimo):>10}"
                f" {fmt_duracao(maximo):>10}"
            )
        else:
            print(f"  {corretor:<{col}} {'0':>8} {'—':>10} {'—':>10} {'—':>10}")

    print(f"{'─' * 72}")

    # Média geral
    todos_tempos = [t for _, ts in por_corretor.items() for t in ts]
    if todos_tempos:
        media_geral = sum(todos_tempos) / len(todos_tempos)
        cor = cor_sla(media_geral)
        print(f"  {BOLD}{'MÉDIA GERAL':<{col}} {len(todos_tempos):>8} {cor}{fmt_duracao(media_geral):>10}{RESET}")
    print(f"{'─' * 72}")


def main():
    args = sys.argv[1:]
    gc = autenticar()

    if "--amostrar" in args:
        amostrar(gc)
        return

    filtro = next((a for a in args if not a.startswith("--")), None)
    calcular_sla(gc, filtro)


if __name__ == "__main__":
    main()
