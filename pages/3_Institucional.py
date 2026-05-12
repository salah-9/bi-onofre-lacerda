"""Dashboard Institucional — Prestação de contas para construtoras parceiras."""

import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent))
import _brand
import _auth
import _gsheets

ROOT = Path(__file__).parent.parent
CLIENT_SECRET = ROOT / "client_secret.json"
TOKEN_DIR = ROOT / ".auth"
SPREADSHEET_ID = "1yPE_XlMWbk1di6xK2bD68w5IbZkVi2JqILC0bXwEykc"

st.set_page_config(
    page_title="Relatório de Campanhas",
    page_icon="📊",
    layout="wide",
)


COR_QUENTE    = "#EF4444"
COR_FRIO      = "#3B82F6"
COR_LIXO      = "#9CA3AF"
COR_VERDE     = "#22C55E"
COR_PRINCIPAL = "#1E6FE8"

FORMATOS = [
    "%d/%m/%Y %H:%M:%S", "%d/%m/%Y %H:%M", "%d/%m/%Y",
    "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d",
]
FORMATOS_SEM_ANO = ["%d/%m %H:%M:%S", "%d/%m %H:%M", "%d/%m"]
HOJE = datetime.today()


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


def mes_ano_label(dt: datetime) -> str:
    meses = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun",
             "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
    return f"{meses[dt.month - 1]}/{dt.year}"


def qualificar(row) -> str:
    if row.get("status", "") == "Perdido":
        return "Descartados"
    return "Quente"


@st.cache_data(ttl=300, show_spinner="Carregando dados...")
def carregar_dados():
    sh = _gsheets.get_spreadsheet()
    raw = sh.worksheet("LeadsConsolidados").get_all_records()

    df = pd.DataFrame(raw)
    df.columns = df.columns.str.strip()

    col_map = {
        "Id Lead":                        "lead_id",
        "Data Criaçao Oportunidade":      "created_at",
        "Tipo do contrato":               "contract_type",
        "Fonte":                          "source",
        "Data Primeira Ação":             "first_action_at",
        "Data Primeiro Contato":          "first_contact_at",
        "Data Ganhou":                    "won_at",
        "Data Perdeu":                    "lost_at",
    }
    df = df.rename(columns={k: v for k, v in col_map.items() if k in df.columns})

    for col in ["created_at", "first_action_at", "first_contact_at", "won_at", "lost_at"]:
        if col in df.columns:
            df[col] = df[col].apply(parse_dt)

    df = df[df["created_at"].notna()].copy()
    df["trimestre"]  = df["created_at"].apply(trimestre)
    df["mes_key"]    = df["created_at"].apply(mes_ano_key)
    df["mes_label"]  = df["created_at"].apply(mes_ano_label)
    df["dia"]        = df["created_at"].dt.date

    df["sla_horas"] = df.apply(
        lambda r: (r["first_contact_at"] - r["created_at"]).total_seconds() / 3600
        if pd.notna(r.get("first_contact_at")) and pd.notna(r.get("created_at"))
        and r["first_contact_at"] > r["created_at"] else None,
        axis=1,
    )

    def status_lead(row):
        if pd.notna(row.get("won_at")):   return "Ganho"
        if pd.notna(row.get("lost_at")):  return "Perdido"
        return "Em aberto"

    df["status"]        = df.apply(status_lead, axis=1)
    df["qualificacao"]  = df.apply(qualificar, axis=1)

    return df


_brand.setup()
_auth.require_login()

# ── Interface ────────────────────────────────────────────────────────────────
st.title("Relatório de Campanhas")
st.caption("Volume de oportunidades · Qualificação de leads · Evolução por período")

df = carregar_dados()

# ── Filtros ───────────────────────────────────────────────────────────────────
trimestres_disp = sorted(df["trimestre"].dropna().unique(), reverse=True)

meses_ord = (
    df[["mes_key", "mes_label"]]
    .drop_duplicates()
    .sort_values("mes_key", ascending=False)
)
meses_labels = meses_ord["mes_label"].tolist()
meses_keys   = meses_ord["mes_key"].tolist()

campanhas_disp = (
    sorted(df["source"].dropna().replace("", pd.NA).dropna().unique().tolist())
    if "source" in df.columns else []
)

col_f1, col_f2, col_f3 = st.columns([2, 2, 3])

with col_f1:
    tipo_periodo = st.selectbox("Período", ["Todos", "Trimestre", "Mês"])

with col_f2:
    if tipo_periodo == "Trimestre":
        trimestre_sel = st.selectbox("Trimestre", trimestres_disp)
        mes_sel_key = None
    elif tipo_periodo == "Mês":
        idx = st.selectbox("Mês", range(len(meses_labels)),
                           format_func=lambda i: meses_labels[i])
        mes_sel_key   = meses_keys[idx]
        trimestre_sel = None
    else:
        trimestre_sel = None
        mes_sel_key   = None

with col_f3:
    campanha_sel = st.multiselect("Campanha", campanhas_disp, placeholder="Todas")

# ── Aplicar filtros ───────────────────────────────────────────────────────────
if tipo_periodo == "Trimestre":
    df_f = df[df["trimestre"] == trimestre_sel].copy()
elif tipo_periodo == "Mês":
    df_f = df[df["mes_key"] == mes_sel_key].copy()
else:
    df_f = df.copy()

if campanha_sel and "source" in df_f.columns:
    df_f = df_f[df_f["source"].isin(campanha_sel)]

# ── KPIs ──────────────────────────────────────────────────────────────────────
st.divider()

total          = len(df_f)
n_quente       = int((df_f["qualificacao"] == "Quente").sum())
n_descartados  = int((df_f["qualificacao"] == "Descartados").sum())
n_convertido   = int((df_f["status"] == "Ganho").sum())
taxa_conv      = n_convertido / total * 100 if total else 0

k1, k2, k3, k4 = st.columns(4)
k1.metric("Total de Oportunidades", f"{total:,}")
k2.metric("Leads Quentes 🔴",       f"{n_quente:,}")
k3.metric("Descartados",            f"{n_descartados:,}")
k4.metric("Taxa de Conversão",      f"{taxa_conv:.1f}%")

st.divider()

# ── Qualificação térmica + Volume por campanha ────────────────────────────────
col_term, col_camp = st.columns([2, 3])

with col_term:
    st.subheader("Qualificação dos Leads")
    st.caption("Quente: em atendimento ou convertido  |  Descartados: leads perdidos")

    fig_termo = go.Figure(go.Pie(
        labels=["Quente", "Descartados"],
        values=[n_quente, n_descartados],
        marker_colors=[COR_QUENTE, COR_LIXO],
        hole=0.5,
        textinfo="label+percent",
        textfont_size=13,
    ))
    fig_termo.update_layout(
        margin=dict(l=0, r=0, t=10, b=0),
        height=320,
        showlegend=False,
    )
    st.plotly_chart(fig_termo, use_container_width=True)

with col_camp:
    st.subheader("Volume de Oportunidades por Campanha")
    st.caption("Top 10 campanhas com mais leads gerados")

    if "source" in df_f.columns:
        camp_vol = (
            df_f["source"]
            .replace("", pd.NA)
            .dropna()
            .value_counts()
            .head(10)
            .reset_index()
        )
        camp_vol.columns = ["Campanha", "Leads"]

        if not camp_vol.empty:
            fig_camp = go.Figure(go.Bar(
                x=camp_vol["Leads"],
                y=camp_vol["Campanha"],
                orientation="h",
                text=camp_vol["Leads"],
                textposition="outside",
                marker_color=COR_PRINCIPAL,
            ))
            fig_camp.update_layout(
                xaxis_title="Oportunidades",
                margin=dict(l=0, r=40, t=0, b=0),
                height=320,
                yaxis=dict(autorange="reversed"),
            )
            st.plotly_chart(fig_camp, use_container_width=True)
        else:
            st.info("Sem dados de campanha para este período.")

st.divider()

# ── Qualificação por campanha (stacked) ───────────────────────────────────────
st.subheader("Qualificação por Campanha")
st.caption("Distribuição de Quentes e Descartados por campanha")

if "source" in df_f.columns:
    camp_qual = (
        df_f[df_f["source"].replace("", pd.NA).notna()]
        .groupby(["source", "qualificacao"])
        .size()
        .reset_index(name="n")
    )

    if not camp_qual.empty:
        top_camps = (
            camp_qual.groupby("source")["n"].sum()
            .nlargest(10).index.tolist()
        )
        camp_qual = camp_qual[camp_qual["source"].isin(top_camps)]

        fig_stack = px.bar(
            camp_qual,
            x="n",
            y="source",
            color="qualificacao",
            orientation="h",
            color_discrete_map={"Quente": COR_QUENTE, "Descartados": COR_LIXO},
            labels={"n": "Leads", "source": "Campanha", "qualificacao": "Qualificação"},
            text_auto=True,
        )
        fig_stack.update_layout(
            margin=dict(l=0, r=0, t=0, b=0),
            height=max(300, len(top_camps) * 40),
            yaxis=dict(autorange="reversed"),
            legend=dict(orientation="h", y=1.05),
        )
        st.plotly_chart(fig_stack, use_container_width=True)

st.divider()

# ── Evolução diária ───────────────────────────────────────────────────────────
st.subheader("Evolução Diária de Oportunidades Geradas")

evolucao = (
    df_f.groupby("dia")
    .size()
    .reset_index(name="leads")
    .sort_values("dia")
)

if not evolucao.empty:
    evolucao["acumulado"] = evolucao["leads"].cumsum()

    fig_evo = go.Figure()

    fig_evo.add_trace(go.Bar(
        x=evolucao["dia"],
        y=evolucao["leads"],
        name="Diário",
        marker_color=COR_PRINCIPAL,
        opacity=0.6,
        yaxis="y",
    ))

    fig_evo.add_trace(go.Scatter(
        x=evolucao["dia"],
        y=evolucao["acumulado"],
        name="Acumulado",
        line=dict(color=COR_VERDE, width=2),
        mode="lines",
        yaxis="y2",
    ))

    fig_evo.update_layout(
        yaxis=dict(title="Leads / dia"),
        yaxis2=dict(title="Acumulado", overlaying="y", side="right", showgrid=False),
        legend=dict(orientation="h", y=1.05),
        margin=dict(l=0, r=0, t=10, b=0),
        height=350,
        hovermode="x unified",
    )
    st.plotly_chart(fig_evo, use_container_width=True)

st.divider()

# ── Evolução por tipo de contrato ─────────────────────────────────────────────
if "contract_type" in df_f.columns:
    st.subheader("Oportunidades por Tipo de Negócio")

    tipo_vol = (
        df_f["contract_type"]
        .replace("", pd.NA)
        .dropna()
        .str.lower()
        .str.strip()
        .value_counts()
        .reset_index()
    )
    tipo_vol.columns = ["Tipo", "Leads"]
    tipo_vol["Tipo"] = tipo_vol["Tipo"].str.capitalize()

    if not tipo_vol.empty:
        fig_tipo = px.pie(
            tipo_vol,
            names="Tipo",
            values="Leads",
            color_discrete_sequence=[COR_PRINCIPAL, COR_VERDE],
            hole=0.4,
        )
        fig_tipo.update_layout(
            margin=dict(l=0, r=0, t=0, b=0),
            height=280,
            legend=dict(orientation="h", y=-0.1),
        )
        col_tipo, _ = st.columns([2, 3])
        with col_tipo:
            st.plotly_chart(fig_tipo, use_container_width=True)

st.caption("Dados atualizados a cada 5 min  ·  Relatório restrito: sem dados financeiros ou de equipe interna")
