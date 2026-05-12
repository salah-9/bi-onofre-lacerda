"""Dashboard Financeiro — Comissões da equipe comercial."""

import sys
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Optional

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent))
import _brand
import _auth
import _gsheets

ROOT = Path(__file__).parent.parent
CLIENT_SECRET = ROOT / "client_secret.json"
TOKEN_DIR     = ROOT / ".auth"
SPREADSHEET_ID = "1yPE_XlMWbk1di6xK2bD68w5IbZkVi2JqILC0bXwEykc"

VGV_GATILHO_PRIME    = Decimal("2100000")
VENDAS_GATILHO_PRIME = 3

st.set_page_config(
    page_title="Dashboard Financeiro",
    page_icon="💰",
    layout="wide",
)


COR_PRIME         = "#22C55E"
COR_PRIME_HERDADO = "#8B5CF6"
COR_BASE          = "#6B7280"
COR_AZUL          = "#1E6FE8"


def parse_brl(val) -> Optional[Decimal]:
    s = str(val).strip()
    if not s:
        return None
    s = s.replace("R$", "").replace(".", "").replace(",", ".").strip()
    try:
        d = Decimal(s)
        return d if d != 0 else None
    except InvalidOperation:
        return None


def fmt_brl(v) -> str:
    if v is None:
        return "—"
    f = float(v)
    return f"R$ {f:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def fmt_pct(v) -> str:
    if v is None:
        return "—"
    return f"{float(v):.0f}%"


@st.cache_data(ttl=300, show_spinner="Carregando dados da planilha...")
def carregar_dados():
    sh = _gsheets.get_spreadsheet()

    rows      = sh.worksheet("OP GANHAS").get_all_records()
    ph_rows   = sh.worksheet("PRIME HERDADO").get_all_records()

    # Corretores com Prime Herdado: set de (corretor, trimestre)
    prime_herdado_set = {
        (str(r.get("Corretor Prime", "")).strip(), str(r.get("Trimestre", "")).strip())
        for r in ph_rows
        if r.get("Corretor Prime") and r.get("Trimestre")
    }

    registros = []
    for row in rows:
        corretor  = str(row.get("Responsavel", "")).strip()
        captador  = str(row.get("Captador", "")).strip() or None
        trimestre = str(row.get("TRIMESTRE", "")).strip()
        tipo      = str(row.get("Tipo de Negocio", "")).strip()

        if not corretor or not trimestre:
            continue

        valor         = parse_brl(row.get("Valor ", row.get("Valor", "")))
        comissao_total = parse_brl(row.get("Comissao Total", ""))
        r_corretor    = parse_brl(row.get("R$ Corretor", ""))
        r_captador    = parse_brl(row.get("R$ Captador", ""))
        pct_corretor  = row.get("% Comissão corretor", "")
        vgv_acum      = parse_brl(row.get("VGV Acumulado", ""))
        categoria     = str(row.get("Categoria Venda", "")).strip()
        prime_flag    = str(row.get("Prime Herdado", "")).strip().upper()
        ordem         = row.get("Ordem da Venda", "")

        # Mês derivado de TRIMESTRE + MES da planilha
        mes_raw = str(row.get("MES", "")).strip()  # formato YYYY-MM
        if not mes_raw and trimestre:
            mes_raw = ""
        _MESES = ["Jan","Fev","Mar","Abr","Mai","Jun","Jul","Ago","Set","Out","Nov","Dez"]
        try:
            ano_m, num_m = mes_raw.split("-")
            mes_label = f"{_MESES[int(num_m)-1]}/{ano_m}"
        except Exception:
            mes_label = mes_raw

        registros.append({
            "corretor":       corretor,
            "captador":       captador,
            "trimestre":      trimestre,
            "mes_key":        mes_raw,
            "mes_label":      mes_label,
            "tipo":           tipo,
            "valor":          valor,
            "comissao_total": comissao_total,
            "r_corretor":     r_corretor,
            "r_captador":     r_captador,
            "pct_corretor":   pct_corretor,
            "vgv_acumulado":  vgv_acum,
            "categoria":      categoria,
            "prime_flag":     prime_flag,
            "ordem":          ordem,
        })

    return pd.DataFrame(registros), prime_herdado_set


def agregar_corretores(df: pd.DataFrame, tipo: str, valor: str, prime_herdado_set: set) -> list[dict]:
    df_t = df.copy()
    resultados = []

    for corretor in sorted(df_t["corretor"].unique()):
        df_c = df_t[df_t["corretor"] == corretor]
        df_vendas   = df_c[df_c["tipo"].str.lower().str.strip() == "venda"]
        df_locacoes = df_c[df_c["tipo"].str.lower().str.strip().str.contains("loca", na=False)]

        num_vendas   = len(df_vendas)
        num_locacoes = len(df_locacoes)

        # VGV = último VGV Acumulado registrado para este corretor
        vgv_vals = df_vendas["vgv_acumulado"].dropna()
        vgv = vgv_vals.max() if not vgv_vals.empty else Decimal("0")

        # Status — usa o trimestre predominante do corretor para checar Prime Herdado
        trimestre_check = df_c["trimestre"].dropna().mode()
        trimestre_check = trimestre_check.iloc[0] if not trimestre_check.empty else ""
        is_prime_herdado = (corretor, trimestre_check) in prime_herdado_set
        atingiu_prime    = "Prime" in df_c["categoria"].values or "SIM" in df_c["prime_flag"].values

        if is_prime_herdado:
            status = "Prime Herdado"
        elif atingiu_prime:
            status = "Prime"
        else:
            status = "Base"

        # Comissões — soma o que já está preenchido na planilha
        r_corretor_total  = df_c["r_corretor"].dropna().sum() or None
        r_captador_total  = df_c["r_captador"].dropna().sum() or None
        comissao_agencia  = df_c["comissao_total"].dropna().sum() or None

        # % do corretor (última taxa registrada para vendas)
        pct_vals = df_vendas["pct_corretor"].replace("", pd.NA).dropna()
        pct_atual = pct_vals.iloc[-1] if not pct_vals.empty else None

        # Progresso para Prime (somente Base)
        prog_vgv  = float(min(vgv / VGV_GATILHO_PRIME, Decimal("1"))) if vgv else 0.0
        prog_vend = min(num_vendas / VENDAS_GATILHO_PRIME, 1.0)
        progresso = max(prog_vgv, prog_vend)

        resultados.append({
            "corretor":         corretor,
            "captador_principal": df_c["captador"].dropna().mode().iloc[0] if not df_c["captador"].dropna().empty else None,
            "status":           status,
            "num_vendas":       num_vendas,
            "num_locacoes":     num_locacoes,
            "vgv":              vgv,
            "comissao_agencia": comissao_agencia,
            "r_corretor":       r_corretor_total,
            "r_captador":       r_captador_total,
            "pct_atual":        pct_atual,
            "progresso":        progresso,
        })

    # Ordena: Prime Herdado → Prime → Base, depois por R$ Corretor
    ordem_status = {"Prime Herdado": 0, "Prime": 1, "Base": 2}
    resultados.sort(key=lambda x: (ordem_status[x["status"]], -(float(x["r_corretor"] or 0))))
    return resultados


# ── Interface ────────────────────────────────────────────────────────────────
_brand.setup()
_auth.require_login()

st.title("Dashboard Financeiro")
st.caption("Comissões · Status Base / Prime · Valor a pagar")

df, prime_herdado_set = carregar_dados()

trimestres = sorted(df["trimestre"].dropna().replace("", pd.NA).dropna().unique(), reverse=True)
if not trimestres:
    st.error("Nenhuma venda encontrada na planilha.")
    st.stop()

meses_ord = (
    df[df["mes_key"] != ""][["mes_key", "mes_label"]]
    .drop_duplicates()
    .sort_values("mes_key", ascending=False)
)
meses_keys   = meses_ord["mes_key"].tolist()
meses_labels = meses_ord["mes_label"].tolist()

col_f1, col_f2, col_f3 = st.columns([2, 2, 3])
with col_f1:
    tipo_periodo = st.selectbox("Período", ["Todos", "Trimestre", "Mês"])
with col_f2:
    if tipo_periodo == "Trimestre":
        periodo_val = st.selectbox("Trimestre", trimestres)
    elif tipo_periodo == "Mês":
        idx = st.selectbox("Mês", range(len(meses_labels)),
                           format_func=lambda i: meses_labels[i])
        periodo_val = meses_keys[idx]
    else:
        periodo_val = None

corretores_disp = sorted(df["corretor"].dropna().replace("", pd.NA).dropna().unique().tolist())
with col_f3:
    corretor_sel = st.multiselect("Corretor", corretores_disp, placeholder="Todos")

if tipo_periodo == "Trimestre":
    df_fil = df[df["trimestre"] == periodo_val]
elif tipo_periodo == "Mês":
    df_fil = df[df["mes_key"] == periodo_val]
else:
    df_fil = df

if corretor_sel:
    df_fil = df_fil[df_fil["corretor"].isin(corretor_sel)]

resultados = agregar_corretores(df_fil, tipo_periodo, periodo_val, prime_herdado_set)

# ── KPIs ──────────────────────────────────────────────────────────────────────
st.divider()

total_vgv        = sum(float(r["vgv"] or 0) for r in resultados)
total_agencia    = sum(float(r["comissao_agencia"] or 0) for r in resultados)
total_corretores = sum(float(r["r_corretor"] or 0) for r in resultados)
n_prime          = sum(1 for r in resultados if r["status"] in ("Prime", "Prime Herdado"))
n_base           = sum(1 for r in resultados if r["status"] == "Base")

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("VGV do Período",            fmt_brl(total_vgv))
k2.metric("Comissão Imobiliária",      fmt_brl(total_agencia))
k3.metric("Total a Pagar Corretores",  fmt_brl(total_corretores))
k4.metric("Corretores Prime 🟢",       n_prime)
k5.metric("Corretores Base ⚪",        n_base)

st.divider()

# ── Cards por corretor ────────────────────────────────────────────────────────
st.subheader("Comissões por Corretor")

BADGE = {
    "Prime Herdado": "🟣 Prime Herdado",
    "Prime":         "🟢 Prime",
    "Base":          "⚪ Base",
}

for r in resultados:
    status  = r["status"]
    corretor = r["corretor"]

    r_corretor_txt = fmt_brl(r["r_corretor"]) if r["r_corretor"] else "⚠️ Pendente"
    pct_txt        = fmt_pct(r["pct_atual"])  if r["pct_atual"] is not None else "—"

    with st.container(border=True):
        col_nome, col_vendas, col_loc, col_vgv, col_imob, col_taxa, col_pagar = st.columns(
            [3, 1, 1, 2, 2, 1, 2]
        )

        with col_nome:
            st.markdown(f"**{corretor}**")
            st.caption(BADGE[status])

        col_vendas.metric("Vendas",     r["num_vendas"])
        col_loc.metric("Locações",     r["num_locacoes"])
        col_vgv.metric("VGV",         fmt_brl(r["vgv"]))
        col_imob.metric("Com. Imob.", fmt_brl(r["comissao_agencia"]))
        col_taxa.metric("Taxa",        pct_txt)
        col_pagar.metric("A Pagar",   fmt_brl(r["r_corretor"]) if r["r_corretor"] else "⚠️ Pendente")

    if status == "Base":
        vgv_f      = float(r["vgv"] or 0)
        falta_vgv  = max(float(VGV_GATILHO_PRIME) - vgv_f, 0)
        falta_vend = max(VENDAS_GATILHO_PRIME - r["num_vendas"], 0)

        if falta_vgv > 0 and falta_vend > 0:
            msg = f"Faltam {fmt_brl(falta_vgv)} em VGV  ou  {falta_vend} venda(s) para Prime"
        else:
            msg = "Atingiu o gatilho — aguardando confirmação Prime"

        st.progress(r["progresso"], text=f"Progresso para Prime — {msg}")

st.divider()

# ── Gráfico VGV por corretor ──────────────────────────────────────────────────
st.subheader("VGV Acumulado por Corretor")

def cor_status(s):
    if s == "Prime Herdado": return COR_PRIME_HERDADO
    if s == "Prime":         return COR_PRIME
    return COR_BASE

nomes  = [r["corretor"] for r in resultados]
vgvs   = [float(r["vgv"] or 0) for r in resultados]
cores  = [cor_status(r["status"]) for r in resultados]
labels = [fmt_brl(r["vgv"]) for r in resultados]

fig = go.Figure(go.Bar(
    x=vgvs, y=nomes,
    orientation="h",
    text=labels, textposition="outside",
    marker_color=cores,
))
fig.add_vline(
    x=float(VGV_GATILHO_PRIME),
    line_dash="dash", line_color=COR_PRIME,
    annotation_text="Meta Prime (R$ 2,1M)",
    annotation_position="top right",
    annotation_font_color=COR_PRIME,
)
fig.update_layout(
    margin=dict(l=0, r=100, t=10, b=0),
    height=max(250, len(resultados) * 45),
    xaxis_title="VGV (R$)",
    yaxis=dict(autorange="reversed"),
)
st.plotly_chart(fig, use_container_width=True)

# ── Gráfico R$ Corretor ───────────────────────────────────────────────────────
st.subheader("Comissão a Pagar por Corretor")

com_vals = [(r["corretor"], float(r["r_corretor"] or 0), cor_status(r["status"])) for r in resultados]
com_vals = [(n, v, c) for n, v, c in com_vals if v > 0]

if com_vals:
    nomes_c, vals_c, cores_c = zip(*com_vals)
    labels_c = [fmt_brl(Decimal(str(v))) for v in vals_c]

    fig2 = go.Figure(go.Bar(
        x=list(vals_c), y=list(nomes_c),
        orientation="h",
        text=labels_c, textposition="outside",
        marker_color=list(cores_c),
    ))
    fig2.update_layout(
        margin=dict(l=0, r=100, t=10, b=0),
        height=max(250, len(com_vals) * 45),
        xaxis_title="R$ Comissão",
        yaxis=dict(autorange="reversed"),
    )
    st.plotly_chart(fig2, use_container_width=True)
else:
    st.info("Nenhuma comissão calculada para este trimestre.")

st.caption("Dados atualizados a cada 5 min · Fonte: OP GANHAS + PRIME HERDADO")
