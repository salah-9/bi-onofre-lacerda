#!/usr/bin/env python3
"""Relatório de comissões por trimestre a partir do CSV de leads.

Uso:
    python3 scripts/relatorio_comissao.py            # trimestre atual
    python3 scripts/relatorio_comissao.py 2025-Q2    # trimestre específico
    python3 scripts/relatorio_comissao.py --all      # todos os trimestres
"""

import csv
import sys
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from commission.calculator import Venda, relatorio_trimestre, trimestre_de_data

# ANSI colors
GREEN  = "\033[32m"
GRAY   = "\033[90m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

CSV_PATH = Path(__file__).parent.parent / "data" / "mock" / "leads.csv"


def carregar_vendas(path: Path) -> list[Venda]:
    vendas = []
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if not row["won_at"] or not row["closed_value"]:
                continue
            vendas.append(Venda(
                lead_id=row["lead_id"],
                corretor=row["final_owner"],
                trimestre=trimestre_de_data(row["won_at"]),
                valor=Decimal(row["closed_value"]),
                contract_type=row["contract_type"],
            ))
    return vendas


def fmt_brl(valor: Decimal) -> str:
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def imprimir_relatorio(trimestre: str, vendas: list[Venda]) -> None:
    resultados = relatorio_trimestre(trimestre, vendas)

    if not resultados:
        print(f"Nenhuma venda encontrada em {trimestre}.")
        return

    col_corretor = max(len(r.corretor) for r in resultados) + 2
    print()
    print(f"{BOLD}{'─' * 70}{RESET}")
    print(f"{BOLD}  Comissões — {trimestre}{RESET}")
    print(f"{'─' * 70}")
    print(
        f"  {'Corretor':<{col_corretor}} {'Status':<8} {'Vendas':>6} "
        f"{'VGV':>18} {'Taxa':>5} {'Comissão':>18}"
    )
    print(f"{'─' * 70}")

    total_vgv = Decimal("0")
    total_comissao = Decimal("0")

    for r in resultados:
        cor = GREEN if r.status == "Prime" else GRAY
        print(
            f"  {cor}{r.corretor:<{col_corretor}} {r.status:<8}{RESET} "
            f"{r.num_vendas:>6} "
            f"{fmt_brl(r.vgv):>18} "
            f"{r.taxa_fmt():>5} "
            f"{fmt_brl(r.comissao):>18}"
        )
        total_vgv += r.vgv
        total_comissao += r.comissao

    print(f"{'─' * 70}")
    print(
        f"  {BOLD}{'TOTAL':<{col_corretor + 9}} "
        f"{fmt_brl(total_vgv):>18}       {fmt_brl(total_comissao):>18}{RESET}"
    )
    print(f"{'─' * 70}")


def trimestres_disponiveis(vendas: list[Venda]) -> list[str]:
    return sorted({v.trimestre for v in vendas})


def trimestre_atual() -> str:
    from datetime import date
    hoje = date.today()
    q = (hoje.month - 1) // 3 + 1
    return f"{hoje.year}-Q{q}"


def main():
    vendas = carregar_vendas(CSV_PATH)
    disponiveis = trimestres_disponiveis(vendas)

    args = sys.argv[1:]

    if "--all" in args:
        for t in disponiveis:
            imprimir_relatorio(t, vendas)
        return

    if args:
        trimestre = args[0]
        if trimestre not in disponiveis:
            print(f"Trimestre '{trimestre}' não encontrado.")
            print(f"Disponíveis: {', '.join(disponiveis)}")
            sys.exit(1)
    else:
        trimestre = trimestre_atual()
        if trimestre not in disponiveis:
            print(f"Nenhum dado para o trimestre atual ({trimestre}).")
            print(f"Disponíveis: {', '.join(disponiveis)}")
            sys.exit(1)

    imprimir_relatorio(trimestre, vendas)


if __name__ == "__main__":
    main()
