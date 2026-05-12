#!/usr/bin/env python3
"""Lê a planilha de leads do Google Sheets e gera relatório de comissões.

Pré-requisito: client_secret.json na raiz do projeto.
Na primeira execução abre o navegador para autorização — após isso usa o token salvo.

Uso:
    python3 scripts/conectar_sheets.py                  # trimestre atual
    python3 scripts/conectar_sheets.py 2025-Q2          # trimestre específico
    python3 scripts/conectar_sheets.py --inspecionar    # mostra colunas da planilha
"""

import csv
import sys
from decimal import Decimal, InvalidOperation
from pathlib import Path

import gspread
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent.parent))

from commission.calculator import Venda, relatorio_trimestre, trimestre_de_data

ROOT = Path(__file__).parent.parent
CLIENT_SECRET = ROOT / "client_secret.json"
TOKEN_DIR = ROOT / ".auth"
SPREADSHEET_ID = "1yPE_XlMWbk1di6xK2bD68w5IbZkVi2JqILC0bXwEykc"

# Mapeamento de colunas da planilha → campos internos
# Ajuste os nomes da esquerda para bater com os cabeçalhos reais da sua planilha
COL_MAP = {
    "lead_id":        ["ID lead", "Id Lead", "lead_id", "id"],
    "won_at":         ["Data Ganhou", "won_at", "data_fechamento"],
    "final_owner":    ["Responsavel", "responsavel final", "Responsável", "final_owner"],
    "closed_value":   ["Valor ", "Valor", "closed_value", "valor_fechado"],
    "contract_type":  ["Tipo de Negocio", "Tipo do contrato", "contract_type", "tipo"],
}


def autenticar() -> gspread.Client:
    if not CLIENT_SECRET.exists():
        print(f"Arquivo não encontrado: {CLIENT_SECRET}")
        print("Baixe o client_secret.json no Google Cloud Console e coloque na pasta imobi/")
        sys.exit(1)

    TOKEN_DIR.mkdir(exist_ok=True)
    gc = gspread.oauth(
        credentials_filename=str(CLIENT_SECRET),
        authorized_user_filename=str(TOKEN_DIR / "token.json"),
    )
    return gc


def resolver_coluna(headers: list, candidatos: list) -> Optional[str]:
    headers_lower = [h.lower().strip() for h in headers]
    for c in candidatos:
        if c.lower() in headers_lower:
            return headers[headers_lower.index(c.lower())]
    return None


def carregar_vendas_sheets(gc: gspread.Client) -> list[Venda]:
    sh = gc.open_by_key(SPREADSHEET_ID)
    ws = sh.worksheet("OP GANHAS")
    registros = ws.get_all_records()

    if not registros:
        print("Planilha vazia ou sem dados.")
        sys.exit(1)

    headers = list(registros[0].keys())

    # Resolve colunas automaticamente
    colunas = {}
    for campo, candidatos in COL_MAP.items():
        col = resolver_coluna(headers, candidatos)
        colunas[campo] = col

    print(f"  Planilha: {sh.title}  ({len(registros)} linhas)")
    print(f"  Mapeamento de colunas:")
    for campo, col in colunas.items():
        status = f"→ '{col}'" if col else "NÃO ENCONTRADO"
        print(f"    {campo:<16} {status}")
    print()

    vendas = []
    ignorados = 0
    for row in registros:
        won_at_raw    = str(row.get(colunas["won_at"] or "", "")).strip()
        valor_raw     = str(row.get(colunas["closed_value"] or "", "")).strip()
        corretor_raw  = str(row.get(colunas["final_owner"] or "", "")).strip()
        tipo_raw      = str(row.get(colunas["contract_type"] or "", "")).strip().lower()
        lead_id_raw   = str(row.get(colunas["lead_id"] or "", "")).strip()

        # Linha sem fechamento → pula
        if not won_at_raw or not valor_raw or not corretor_raw:
            ignorados += 1
            continue

        # Normaliza valor: remove R$, pontos de milhar, troca vírgula por ponto
        valor_clean = (
            valor_raw
            .replace("R$", "")
            .replace(".", "")
            .replace(",", ".")
            .strip()
        )
        try:
            valor = Decimal(valor_clean)
        except InvalidOperation:
            ignorados += 1
            continue

        # Normaliza data (aceita YYYY-MM-DD ou DD/MM/YYYY)
        if "/" in won_at_raw:
            partes = won_at_raw.split("/")
            won_at = f"{partes[2]}-{partes[1]}-{partes[0]}T00:00:00"
        elif "T" not in won_at_raw:
            won_at = won_at_raw + "T00:00:00"
        else:
            won_at = won_at_raw

        try:
            trimestre = trimestre_de_data(won_at)
        except Exception:
            ignorados += 1
            continue

        contract_type = "locação" if "loca" in tipo_raw else "venda"

        vendas.append(Venda(
            lead_id=lead_id_raw,
            corretor=corretor_raw,
            trimestre=trimestre,
            valor=valor,
            contract_type=contract_type,
        ))

    print(f"  Vendas carregadas: {len(vendas)}  |  Ignoradas (sem fechamento): {ignorados}")
    print()
    return vendas


def inspecionar(gc: gspread.Client) -> None:
    sh = gc.open_by_key(SPREADSHEET_ID)
    for i, ws in enumerate(sh.worksheets()):
        print(f"Aba {i}: '{ws.title}'  ({ws.row_count} linhas x {ws.col_count} colunas)")
        primeira_linha = ws.row_values(1)
        print(f"  Cabeçalhos: {primeira_linha}")
    print()


# ANSI colors
GREEN = "\033[32m"
GRAY  = "\033[90m"
BOLD  = "\033[1m"
RESET = "\033[0m"


def fmt_brl(valor: Decimal) -> str:
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def imprimir_relatorio(trimestre: str, vendas: list[Venda]) -> None:
    resultados = relatorio_trimestre(trimestre, vendas)
    if not resultados:
        print(f"Nenhuma venda encontrada em {trimestre}.")
        return

    col = max(len(r.corretor) for r in resultados) + 2
    print(f"{BOLD}{'─' * 70}{RESET}")
    print(f"{BOLD}  Comissões — {trimestre}{RESET}")
    print(f"{'─' * 70}")
    print(f"  {'Corretor':<{col}} {'Status':<8} {'Vendas':>6} {'VGV':>18} {'Taxa':>5} {'Comissão':>18}")
    print(f"{'─' * 70}")

    total_vgv = total_com = Decimal("0")
    for r in resultados:
        cor = GREEN if r.status == "Prime" else GRAY
        print(
            f"  {cor}{r.corretor:<{col}} {r.status:<8}{RESET}"
            f" {r.num_vendas:>6} {fmt_brl(r.vgv):>18} {r.taxa_fmt():>5} {fmt_brl(r.comissao):>18}"
        )
        total_vgv += r.vgv
        total_com += r.comissao

    print(f"{'─' * 70}")
    print(f"  {BOLD}{'TOTAL':<{col + 9}} {fmt_brl(total_vgv):>18}       {fmt_brl(total_com):>18}{RESET}")
    print(f"{'─' * 70}")


def trimestre_atual() -> str:
    from datetime import date
    d = date.today()
    return f"{d.year}-Q{(d.month - 1) // 3 + 1}"


def main():
    args = sys.argv[1:]
    gc = autenticar()

    if "--inspecionar" in args:
        inspecionar(gc)
        return

    vendas = carregar_vendas_sheets(gc)
    trimestres = sorted({v.trimestre for v in vendas})

    if not trimestres:
        print("Nenhuma venda com fechamento encontrada na planilha.")
        return

    if "--all" in args:
        for t in trimestres:
            imprimir_relatorio(t, vendas)
        return

    if args:
        t = args[0]
        if t not in trimestres:
            print(f"Trimestre '{t}' não encontrado. Disponíveis: {', '.join(trimestres)}")
            sys.exit(1)
    else:
        t = trimestre_atual()
        if t not in trimestres:
            t = trimestres[-1]
            print(f"Usando trimestre mais recente com dados: {t}\n")

    imprimir_relatorio(t, vendas)


if __name__ == "__main__":
    main()
