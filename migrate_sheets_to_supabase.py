"""
Migração one-time: Google Sheets → Supabase

Uso:
    export SUPABASE_URL="https://xxxx.supabase.co"
    export SUPABASE_KEY="sua-service-role-key"
    python migrate_sheets_to_supabase.py
"""

import os
import sys
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Optional

# ── Dependências ───────────────────────────────────────────────────────────────
try:
    import gspread
    from google.oauth2.credentials import Credentials as OAuthCreds
    from google.auth.transport.requests import Request
    from supabase import create_client
except ImportError as e:
    print(f"Dependência faltando: {e}")
    print("Execute: pip install gspread google-auth supabase")
    sys.exit(1)

# ── Configuração ───────────────────────────────────────────────────────────────
SPREADSHEET_ID = "1yPE_XlMWbk1di6xK2bD68w5IbZkVi2JqILC0bXwEykc"
TOKEN_DIR      = Path(__file__).parent / ".auth"
CLIENT_SECRET  = Path(__file__).parent / "client_secret.json"
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

FORMATOS = [
    "%d/%m/%Y %H:%M:%S", "%d/%m/%Y %H:%M", "%d/%m/%Y",
    "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d",
]
FORMATOS_SEM_ANO = ["%d/%m %H:%M:%S", "%d/%m %H:%M", "%d/%m"]
HOJE = datetime.today()


def _inferir_ano(dia, mes):
    for ano in (HOJE.year, HOJE.year - 1):
        try:
            if datetime(ano, mes, dia) <= HOJE:
                return ano
        except ValueError:
            pass
    return HOJE.year - 1


def _parse_dt(valor) -> Optional[str]:
    s = str(valor).strip()
    if not s:
        return None
    for fmt in FORMATOS:
        try:
            return datetime.strptime(s, fmt).strftime("%Y-%m-%dT%H:%M:%S")
        except ValueError:
            pass
    for fmt in FORMATOS_SEM_ANO:
        try:
            dt = datetime.strptime(s, fmt)
            dt = dt.replace(year=_inferir_ano(dt.day, dt.month))
            return dt.strftime("%Y-%m-%dT%H:%M:%S")
        except ValueError:
            pass
    return None


def _parse_brl(val) -> Optional[float]:
    s = str(val).strip()
    if not s:
        return None
    s = s.replace("R$", "").replace(".", "").replace(",", ".").strip()
    try:
        d = Decimal(s)
        return float(d) if d != 0 else None
    except InvalidOperation:
        return None


def _text(val) -> Optional[str]:
    s = str(val).strip() if val is not None else ""
    return s or None


# ── Conexão Google Sheets ──────────────────────────────────────────────────────
def _get_sheets_client():
    token_path = TOKEN_DIR / "token.json"
    if token_path.exists():
        import json
        t = json.loads(token_path.read_text())
        creds = OAuthCreds(
            token=None,
            refresh_token=t["refresh_token"],
            token_uri=t["token_uri"],
            client_id=t["client_id"],
            client_secret=t["client_secret"],
            scopes=t["scopes"],
        )
        creds.refresh(Request())
        return gspread.authorize(creds)

    return gspread.oauth(
        credentials_filename=str(CLIENT_SECRET),
        authorized_user_filename=str(token_path),
    )


# ── Conexão Supabase ───────────────────────────────────────────────────────────
def _get_supabase():
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    if not url or not key:
        print("SUPABASE_URL e SUPABASE_KEY precisam estar definidos como variáveis de ambiente.")
        sys.exit(1)
    return create_client(url, key)


# ── Migração leads_consolidados ────────────────────────────────────────────────
def migrate_leads(sh, sb):
    print("→ Migrando LeadsConsolidados...")
    rows = sh.worksheet("LeadsConsolidados").get_all_records()
    print(f"  {len(rows)} registros encontrados na planilha.")

    registros = []
    for row in rows:
        registros.append({
            "lead_id":          _text(row.get("Id Lead")),
            "created_at":       _parse_dt(row.get("Data Criaçao Oportunidade") or row.get("Data Criação Oportunidade", "")),
            "client_name":      _text(row.get("Nome")),
            "client_email":     _text(row.get("Email")),
            "initial_owner":    _text(row.get("Responsável") or row.get("Responsavel")),
            "final_owner":      _text(row.get("responsavel final")),
            "contract_type":    _text(row.get("Tipo do contrato")),
            "source":           _text(row.get("Fonte")),
            "first_action_at":  _parse_dt(row.get("Data Primeira Ação", "")),
            "first_contact_at": _parse_dt(row.get("Data Primeiro Contato", "")),
            "won_at":           _parse_dt(row.get("Data Ganhou", "")),
            "lost_at":          _parse_dt(row.get("Data Perdeu", "")),
            "loss_reason":      _text(row.get("Motivo Perda")),
            "regiao":           _text(row.get("Regiao")),
        })

    # Upsert em lotes de 500
    batch = 500
    for i in range(0, len(registros), batch):
        sb.table("leads_consolidados").upsert(registros[i:i+batch]).execute()
        print(f"  inserido lote {i//batch + 1} ({min(i+batch, len(registros))}/{len(registros)})")
    print(f"  ✓ leads_consolidados concluído.\n")


# ── Migração op_ganhas ─────────────────────────────────────────────────────────
def migrate_op_ganhas(sh, sb):
    print("→ Migrando OP GANHAS...")
    rows = sh.worksheet("OP GANHAS").get_all_records()
    print(f"  {len(rows)} registros encontrados na planilha.")

    _MESES = ["Jan","Fev","Mar","Abr","Mai","Jun","Jul","Ago","Set","Out","Nov","Dez"]

    def _normalizar_tipo_imovel(val: str) -> str:
        s = val.lower().strip()
        if any(k in s for k in ("novo", "lança", "lanca", "planta", "constru")):
            return "Novo"
        if any(k in s for k in ("usado", "revendas", "revenda", "segunda")):
            return "Usado"
        return val.title() if val else ""

    registros = []
    for row in rows:
        corretor  = _text(row.get("Responsavel"))
        trimestre = _text(row.get("TRIMESTRE"))
        if not corretor or not trimestre:
            continue

        mes_raw = str(row.get("MES", "")).strip()

        registros.append({
            "lead_id":            _text(row.get("ID lead")),
            "won_at":             _parse_dt(row.get("Data Ganhou", "")),
            "corretor":           corretor,
            "captador":           _text(row.get("Captador")),
            "trimestre":          trimestre,
            "mes":                mes_raw or None,
            "tipo_negocio":       _text(row.get("Tipo de Negocio")),
            "tipo_imovel":        _normalizar_tipo_imovel(str(row.get("Tipo de Imovel", row.get("Tipo", "")))),
            "regiao":             _text(row.get("Regiao")),
            "valor":              _parse_brl(row.get("Valor ", row.get("Valor", ""))),
            "comissao_total":     _parse_brl(row.get("Comissao Total", "")),
            "r_corretor":         _parse_brl(row.get("R$ Corretor", "")),
            "r_captador":         _parse_brl(row.get("R$ Captador", "")),
            "r_gestao":           _parse_brl(row.get("R$ dayvson coord", "")),
            "vgv_acumulado":      _parse_brl(row.get("VGV Acumulado", "")),
            "categoria_venda":    _text(row.get("Categoria Venda")),
            "prime_herdado_flag": _text(row.get("Prime Herdado")),
        })

    batch = 500
    for i in range(0, len(registros), batch):
        sb.table("op_ganhas").upsert(registros[i:i+batch]).execute()
        print(f"  inserido lote {i//batch + 1} ({min(i+batch, len(registros))}/{len(registros)})")
    print(f"  ✓ op_ganhas concluído.\n")


# ── Migração prime_herdado ─────────────────────────────────────────────────────
def migrate_prime_herdado(sh, sb):
    print("→ Migrando PRIME HERDADO...")
    rows = sh.worksheet("PRIME HERDADO").get_all_records()
    print(f"  {len(rows)} registros encontrados na planilha.")

    registros = [
        {
            "corretor_prime": _text(r.get("Corretor Prime")),
            "trimestre":      _text(r.get("Trimestre")),
        }
        for r in rows
        if r.get("Corretor Prime") and r.get("Trimestre")
    ]

    if registros:
        sb.table("prime_herdado").upsert(registros).execute()
    print(f"  ✓ prime_herdado concluído ({len(registros)} registros).\n")


# ── Main ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("Conectando ao Google Sheets...")
    gc = _get_sheets_client()
    sh = gc.open_by_key(SPREADSHEET_ID)
    print("Conectando ao Supabase...")
    sb = _get_supabase()

    migrate_leads(sh, sb)
    migrate_op_ganhas(sh, sb)
    migrate_prime_herdado(sh, sb)

    print("Migração concluída!")
