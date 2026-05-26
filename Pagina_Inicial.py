"""BI Onofre Lacerda — App unificado com tabs, sem sidebar."""

import sys
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Optional

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

sys.path.insert(0, str(Path(__file__).parent))
import _auth
import _gsheets

import base64 as _base64

st.set_page_config(
    page_title="Onofre Lacerda — BI",
    page_icon=str(Path(__file__).parent / "assets" / "MARCA REDUÇÃO_01.png"),
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Auth antes de qualquer carregamento pesado
_auth.require_login()

AZUL      = "#184D6C"
CREME     = "#FFFBD6"
AZUL_DARK = "#0d1e2d"
AZUL_CARD = "#163d55"

# ── Fontes via base64 (cacheado — lê arquivos só uma vez) ─────────────────────
def _b64f(path):
    try:
        return _base64.b64encode(Path(path).read_bytes()).decode()
    except Exception:
        return ""

_ROOT = Path(__file__).parent
_ff = lambda n, b, fmt, w: (
    f"@font-face{{font-family:'{n}';src:url('data:font/{fmt};base64,{b}') "
    f"format('{fmt}');font-weight:{w};font-display:swap;}}" if b else ""
)

@st.cache_resource
def _carregar_font_css():
    return (
        _ff("TrajanPro", _b64f(_ROOT/"fonts/trajan/TrajanPro-Regular.ttf"), "truetype", 400) +
        _ff("TrajanPro", _b64f(_ROOT/"fonts/trajan/TrajanPro-Bold.otf"),    "opentype", 700) +
        _ff("SwitzCond", _b64f(_ROOT/"fonts/switzerland/Switzerland_Condensed_Plain.ttf"), "truetype", 400) +
        _ff("SwitzCond", _b64f(_ROOT/"fonts/switzerland/Switzerland_Condensed_Bold.ttf"),  "truetype", 700)
    )

st.markdown(f"<style>{_carregar_font_css()}</style>", unsafe_allow_html=True)

# ── CSS principal ─────────────────────────────────────────────────────────────
st.markdown(f"""
<style>
[data-testid="stToolbar"] {{display:none !important;}}
header[data-testid="stHeader"] {{display:none !important;}}
section[data-testid="stSidebar"] {{display:none !important;}}

.stApp, .main .block-container {{
    background-color: {AZUL_DARK} !important;
    color: {CREME} !important;
}}
h1 {{
    font-family: 'TrajanPro', serif !important;
    color: {CREME} !important;
    letter-spacing: 0.06em !important;
    font-size: 1.4rem !important;
    border-bottom: 1px solid rgba(255,251,214,0.15);
    padding-bottom: 0.4rem;
}}
h2, h3 {{
    font-family: 'TrajanPro', serif !important;
    color: {CREME} !important;
    letter-spacing: 0.05em !important;
}}
p, span, label, div, small {{
    font-family: 'SwitzCond', sans-serif !important;
}}
[data-testid="stMetricValue"] {{
    color: {CREME} !important;
    font-family: 'SwitzCond', sans-serif !important;
    font-weight: 700 !important;
    font-size: 1.2rem !important;
    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
}}
[data-testid="stMetricLabel"] {{
    color: rgba(255,251,214,0.55) !important;
    font-family: 'SwitzCond', sans-serif !important;
    font-size: 0.64rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.07em !important;
}}
[data-testid="stVerticalBlockBorderWrapper"] > div {{
    background-color: {AZUL_CARD} !important;
    border: 1px solid rgba(255,251,214,0.1) !important;
    border-radius: 6px !important;
}}
hr {{border-color: rgba(255,251,214,0.12) !important;}}
[data-testid="stTabs"] [role="tab"] {{
    color: rgba(255,251,214,0.45) !important;
    font-family: 'SwitzCond', sans-serif !important;
    letter-spacing: 0.08em !important;
    font-size: 0.82rem !important;
    text-transform: uppercase !important;
}}
[data-testid="stTabs"] [role="tab"][aria-selected="true"] {{
    color: {CREME} !important;
    border-bottom: 2px solid {CREME} !important;
}}
[data-testid="stSelectbox"] label,
[data-testid="stMultiSelect"] label {{
    color: rgba(255,251,214,0.65) !important;
    font-family: 'SwitzCond', sans-serif !important;
    font-size: 0.7rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.06em !important;
}}
[data-testid="stSelectbox"] > div > div,
[data-testid="stMultiSelect"] > div > div {{
    background-color: {AZUL_CARD} !important;
    border: 1px solid rgba(255,251,214,0.18) !important;
    color: {CREME} !important;
}}
.stCaption, [data-testid="stCaptionContainer"] * {{
    color: rgba(255,251,214,0.45) !important;
    font-family: 'SwitzCond', sans-serif !important;
}}
.stButton > button {{
    background-color: {CREME} !important;
    color: {AZUL} !important;
    border: none !important;
    font-family: 'SwitzCond', sans-serif !important;
    font-weight: 700 !important;
    letter-spacing: 0.06em !important;
    border-radius: 3px !important;
}}
[data-testid="stProgress"] > div > div {{
    background-color: {CREME} !important;
    opacity: 0.55 !important;
}}
.ol-section {{
    border-left: 3px solid {CREME};
    padding: 0.45rem 0.9rem;
    margin: 1.8rem 0 0.8rem 0;
    background: rgba(255,251,214,0.03);
    border-radius: 0 4px 4px 0;
}}
.ol-section-title {{
    font-family: 'TrajanPro', serif !important;
    letter-spacing: 0.1em;
    font-size: 0.75rem;
    text-transform: uppercase;
    font-weight: 700;
    margin: 0;
    color: {CREME} !important;
}}
.ol-section-sub {{
    font-family: 'SwitzCond', sans-serif !important;
    font-size: 0.68rem;
    margin: 0.08rem 0 0 0;
    color: rgba(255,251,214,0.45) !important;
}}
@media (max-width: 768px) {{
    .main .block-container {{padding: 0.75rem !important; max-width: 100% !important;}}
    div[data-testid="stHorizontalBlock"] {{flex-wrap: wrap !important;}}
    div[data-testid="column"] {{min-width: calc(50% - 0.5rem) !important;}}
}}
</style>
""", unsafe_allow_html=True)

# ── Header com logo ───────────────────────────────────────────────────────────
_logo_path = _ROOT / "assets" / "marca_horizontal_crop.png"
if _logo_path.exists():
    _logo_b64 = _b64f(_logo_path)
    st.markdown(
        f'<div style="text-align:center;padding:2.5rem 0 1.5rem 0;">'
        f'<div style="'
        f'display:inline-block;'
        f'background:#ffffff;'
        f'border-radius:16px;'
        f'box-shadow:'
        f'0 20px 60px rgba(0,0,0,0.5),'
        f'0 6px 20px rgba(0,0,0,0.3);'
        f'padding:1.8rem 3.5rem;">'
        f'<img src="data:image/png;base64,{_logo_b64}" '
        f'style="height:90px;display:block;">'
        f'</div></div>',
        unsafe_allow_html=True,
    )

st.divider()

# ── Shared helpers ─────────────────────────────────────────────────────────────
FORMATOS = [
    "%d/%m/%Y %H:%M:%S", "%d/%m/%Y %H:%M", "%d/%m/%Y",
    "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d",
]
FORMATOS_SEM_ANO = ["%d/%m %H:%M:%S", "%d/%m %H:%M", "%d/%m"]
HOJE = datetime.today()

def inferir_ano(dia, mes):
    for ano in (HOJE.year, HOJE.year - 1):
        try:
            if datetime(ano, mes, dia) <= HOJE: return ano
        except ValueError: pass
    return HOJE.year - 1

def parse_dt(valor):
    s = str(valor).strip()
    if not s: return None
    for fmt in FORMATOS:
        try: return datetime.strptime(s, fmt)
        except ValueError: pass
    for fmt in FORMATOS_SEM_ANO:
        try:
            dt = datetime.strptime(s, fmt)
            return dt.replace(year=inferir_ano(dt.day, dt.month))
        except ValueError: pass
    return None

def trimestre_de_dt(dt): return f"{dt.year}-Q{(dt.month-1)//3+1}"
def mes_key(dt): return dt.strftime("%Y-%m")
def mes_label(dt):
    meses = ["Jan","Fev","Mar","Abr","Mai","Jun","Jul","Ago","Set","Out","Nov","Dez"]
    return f"{meses[dt.month-1]}/{dt.year}"

# ── TABS ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["Comercial", "Financeiro", "Institucional"])

# ─────────────────────────────────────────────────────────────────
# COMERCIAL
# ─────────────────────────────────────────────────────────────────
COR_PRINCIPAL = '#1E6FE8'
COR_VERDE     = '#22C55E'
COR_AMARELO   = '#F59E0B'
COR_VERMELHO  = '#EF4444'
COR_CINZA     = '#6B7280'

@st.cache_data(ttl=300, show_spinner=False)
def com_carregar_dados():
    sh = _gsheets.get_spreadsheet()

    leads_raw = sh.worksheet("LeadsConsolidados").get_all_records()
    ganhas_raw = sh.worksheet("OP GANHAS").get_all_records()

    leads = pd.DataFrame(leads_raw)
    leads.columns = leads.columns.str.strip()

    col_map_leads = {
        "Id Lead": "lead_id",
        "Data Criaçao Oportunidade": "created_at",
        "Nome": "client_name",
        "Responsável": "initial_owner",
        "responsavel final": "final_owner",
        "Tipo do contrato": "contract_type",
        "Fonte": "source",
        "Data Primeira Ação": "first_action_at",
        "Data Primeiro Contato": "first_contact_at",
        "Data Ganhou": "won_at",
        "Data Perdeu": "lost_at",
        "Motivo Perda": "loss_reason",
        "Regiao": "regiao",
    }
    leads = leads.rename(columns={k: v for k, v in col_map_leads.items() if k in leads.columns})
    if "regiao" in leads.columns:
        leads["regiao"] = leads["regiao"].astype(str).str.strip().str.title().replace("", pd.NA)

    for col in ["created_at", "first_action_at", "first_contact_at", "won_at", "lost_at"]:
        if col in leads.columns:
            leads[col] = leads[col].apply(parse_dt)

    leads = leads[leads["created_at"].notna()].copy()
    leads["trimestre"] = leads["created_at"].apply(trimestre_de_dt)
    leads["mes_key"]   = leads["created_at"].apply(mes_key)
    leads["mes_label"] = leads["created_at"].apply(mes_label)

    leads["sla_horas"] = leads.apply(
        lambda r: (r["first_contact_at"] - r["created_at"]).total_seconds() / 3600
        if pd.notna(r.get("first_contact_at")) and pd.notna(r.get("created_at"))
        and r["first_contact_at"] > r["created_at"] else None,
        axis=1,
    )

    leads["acao_horas"] = leads.apply(
        lambda r: (r["first_action_at"] - r["created_at"]).total_seconds() / 3600
        if pd.notna(r.get("first_action_at")) and pd.notna(r.get("created_at"))
        and r["first_action_at"] > r["created_at"] else None,
        axis=1,
    )

    leads["ciclo_dias"] = leads.apply(
        lambda r: (r["won_at"] - r["created_at"]).total_seconds() / 86400
        if pd.notna(r.get("won_at")) and pd.notna(r.get("created_at"))
        and r["won_at"] > r["created_at"] else None,
        axis=1,
    )

    def status_lead(row):
        if pd.notna(row.get("won_at")):
            return "Ganho"
        if pd.notna(row.get("lost_at")):
            return "Perdido"
        return "Em aberto"

    leads["status"] = leads.apply(status_lead, axis=1)

    ganhas = pd.DataFrame(ganhas_raw)
    ganhas.columns = ganhas.columns.str.strip()

    col_map_ganhas = {
        "ID lead": "lead_id",
        "Data Ganhou": "won_at",
        "Responsavel": "corretor",
        "Valor": "valor",
        "Tipo de Negocio": "contract_type",
        "Regiao": "regiao",
    }
    ganhas = ganhas.rename(columns={k: v for k, v in col_map_ganhas.items() if k in ganhas.columns})
    if "regiao" in ganhas.columns:
        ganhas["regiao"] = ganhas["regiao"].astype(str).str.strip().str.title().replace("", pd.NA)

    if "valor" in ganhas.columns:
        ganhas["valor"] = (
            ganhas["valor"].astype(str)
            .str.replace("R$", "", regex=False)
            .str.replace(".", "", regex=False)
            .str.replace(",", ".", regex=False)
            .str.strip()
        )
        ganhas["valor"] = pd.to_numeric(ganhas["valor"], errors="coerce")

    if "won_at" in ganhas.columns:
        ganhas["won_at"] = ganhas["won_at"].apply(parse_dt)

    ganhas = ganhas[ganhas["won_at"].notna()].copy()
    ganhas["trimestre"] = ganhas["won_at"].apply(trimestre_de_dt)
    ganhas["mes_key"]   = ganhas["won_at"].apply(mes_key)
    ganhas = ganhas[ganhas["contract_type"].str.lower().str.strip() != "locação"]

    return leads, ganhas



with tab1:
    
    # ── Interface ────────────────────────────────────────────────────────────────
    st.title("Dashboard Comercial")
    
    leads, ganhas = com_carregar_dados()
    
    # ── Filtros ───────────────────────────────────────────────────────────────────
    trimestres_disp = sorted(leads["trimestre"].dropna().unique(), reverse=True)
    
    meses_ord = (
        leads[["mes_key", "mes_label"]]
        .drop_duplicates()
        .sort_values("mes_key", ascending=False)
    )
    meses_labels = meses_ord["mes_label"].tolist()
    meses_keys   = meses_ord["mes_key"].tolist()
    
    corretores_disp = sorted(
        leads["initial_owner"].dropna().replace("", pd.NA).dropna().unique().tolist(),
        key=str,
    )
    campanhas_disp = (
        sorted(leads["source"].dropna().replace("", pd.NA).dropna().unique().tolist(), key=str)
        if "source" in leads.columns else []
    )
    regioes_disp = (
        sorted(leads["regiao"].dropna().replace("", pd.NA).dropna().unique().tolist(), key=str)
        if "regiao" in leads.columns else []
    )

    col_f1, col_f2, col_f3, col_f4, col_f5 = st.columns([2, 2, 2, 3, 3])

    with col_f1:
        tipo_periodo = st.selectbox("Período", ["Todos", "Trimestre", "Mês"], key="com_per_odo")

    with col_f2:
        if tipo_periodo == "Trimestre":
            trimestre_sel = st.selectbox("Trimestre", trimestres_disp, key="com_trimestre")
            mes_sel_key = None
        elif tipo_periodo == "Mês":
            mes_idx = st.selectbox("Mês", range(len(meses_labels)), key="com_m_s",
                                   format_func=lambda i: meses_labels[i])
            mes_sel_key = meses_keys[mes_idx]
            trimestre_sel = None
        else:
            trimestre_sel = None
            mes_sel_key = None

    with col_f3:
        regiao_sel = st.multiselect("Região", regioes_disp, placeholder="Todas", key="com_regiao")

    with col_f4:
        corretor_sel = st.multiselect("Corretor", corretores_disp, placeholder="Todos", key="com_corretor")

    with col_f5:
        campanha_sel = st.multiselect("Campanha", campanhas_disp, placeholder="Todas", key="com_campanha")

    # ── Aplicar filtros ───────────────────────────────────────────────────────────
    if tipo_periodo == "Trimestre":
        leads_f  = leads[leads["trimestre"] == trimestre_sel].copy()
        ganhas_f = ganhas[ganhas["trimestre"] == trimestre_sel].copy()
    elif tipo_periodo == "Mês":
        leads_f  = leads[leads["mes_key"] == mes_sel_key].copy()
        ganhas_f = ganhas[ganhas["mes_key"] == mes_sel_key].copy()
    else:
        leads_f  = leads.copy()
        ganhas_f = ganhas.copy()

    if regiao_sel:
        if "regiao" in leads_f.columns:
            leads_f = leads_f[leads_f["regiao"].isin(regiao_sel)]
        if "regiao" in ganhas_f.columns:
            ganhas_f = ganhas_f[ganhas_f["regiao"].isin(regiao_sel)]

    if corretor_sel:
        leads_f = leads_f[leads_f["initial_owner"].isin(corretor_sel)]
        if "corretor" in ganhas_f.columns:
            ganhas_f = ganhas_f[ganhas_f["corretor"].isin(corretor_sel)]

    if campanha_sel and "source" in leads_f.columns:
        leads_f = leads_f[leads_f["source"].isin(campanha_sel)]
    
    # ── KPIs principais ───────────────────────────────────────────────────────────
    st.divider()
    
    total_leads    = len(leads_f)
    total_ganhos   = int((leads_f["status"] == "Ganho").sum())
    total_perdidos = int((leads_f["status"] == "Perdido").sum())
    em_aberto      = int((leads_f["status"] == "Em aberto").sum())
    conv_rate      = total_ganhos / total_leads * 100 if total_leads else 0
    
    sla_valido   = leads_f["sla_horas"].dropna()
    sla_medio    = sla_valido.mean() if len(sla_valido) else None
    
    acao_valido  = leads_f["acao_horas"].dropna() if "acao_horas" in leads_f.columns else pd.Series(dtype=float)
    acao_medio   = acao_valido.mean() if len(acao_valido) else None
    
    ciclo_valido = leads_f["ciclo_dias"].dropna() if "ciclo_dias" in leads_f.columns else pd.Series(dtype=float)
    ciclo_medio  = ciclo_valido.mean() if len(ciclo_valido) else None
    
    ticket_medio = ganhas_f["valor"].mean() if not ganhas_f.empty and "valor" in ganhas_f.columns else None
    
    
    def fmt_sla(h):
        if h is None:
            return "—"
        if h < 1:
            return f"{int(h * 60)}min"
        if h < 24:
            return f"{h:.1f}h"
        return f"{int(h // 24)}d {h % 24:.0f}h"
    
    
    def fmt_dias(d):
        if d is None:
            return "—"
        if d < 1:
            return f"{int(d * 24)}h"
        return f"{d:.1f} dias"
    
    
    def fmt_brl(v):
        if v is None or (isinstance(v, float) and pd.isna(v)):
            return "—"
        return f"R$ {v:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")
    
    
    def cor_sla(h):
        if h <= 2:
            return COR_VERDE
        if h <= 24:
            return COR_AMARELO
        return COR_VERMELHO
    
    
    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Total de Leads",    f"{total_leads:,}")
    k2.metric("Ganhos",            f"{total_ganhos:,}")
    k3.metric("Perdidos",          f"{total_perdidos:,}")
    k4.metric("Em Aberto",         f"{em_aberto:,}")
    k5.metric("Taxa de Conversão", f"{conv_rate:.1f}%")
    
    k6, k7, k8, k9 = st.columns(4)
    k6.metric("SLA Médio 1º Contato", fmt_sla(sla_medio))
    k7.metric("Tempo Médio 1ª Ação",  fmt_sla(acao_medio))
    k8.metric("Ciclo Médio de Venda", fmt_dias(ciclo_medio))
    k9.metric("Ticket Médio",         fmt_brl(ticket_medio))
    
    st.divider()
    
    # ── Funil + Pizza ─────────────────────────────────────────────────────────────
    col_funil, col_resultado = st.columns([3, 2])
    
    with col_funil:
        st.subheader("Funil de Conversão")
    
        tem_first_action  = int(leads_f["first_action_at"].notna().sum()) if "first_action_at" in leads_f else 0
        tem_first_contact = int(leads_f["first_contact_at"].notna().sum()) if "first_contact_at" in leads_f else 0
    
        fig_funil = go.Figure(go.Funnel(
            y=["Leads Gerados", "1ª Ação", "1º Contato", "Ganhos"],
            x=[total_leads, tem_first_action, tem_first_contact, total_ganhos],
            textinfo="value+percent initial",
            marker=dict(color=[COR_PRINCIPAL, "#4B8EF1", "#7FB3FF", COR_VERDE]),
        ))
        fig_funil.update_layout(margin=dict(l=0, r=0, t=0, b=0), height=300)
        st.plotly_chart(fig_funil, use_container_width=True)
    
    with col_resultado:
        st.subheader("Resultado dos Leads")
    
        fig_pizza = px.pie(
            values=[total_ganhos, total_perdidos, em_aberto],
            names=["Ganhos", "Perdidos", "Em Aberto"],
            color_discrete_sequence=[COR_VERDE, COR_VERMELHO, COR_CINZA],
            hole=0.45,
        )
        fig_pizza.update_layout(
            margin=dict(l=0, r=0, t=0, b=0),
            height=300,
            legend=dict(orientation="h", y=-0.1),
        )
        st.plotly_chart(fig_pizza, use_container_width=True)
    
    st.divider()
    
    # ── SLA 1º Contato + Tempo 1ª Ação ───────────────────────────────────────────
    col_sla, col_acao = st.columns(2)
    
    with col_sla:
        st.subheader("SLA — 1º Contato por Corretor")
    
        sla_rank = (
            leads_f[leads_f["sla_horas"].notna() & leads_f["initial_owner"].notna()]
            .groupby("initial_owner")["sla_horas"]
            .mean()
            .reset_index()
            .rename(columns={"initial_owner": "Corretor", "sla_horas": "media"})
            .sort_values("media")
        )
    
        if not sla_rank.empty:
            sla_rank["label"] = sla_rank["media"].apply(fmt_sla)
            sla_rank["cor"]   = sla_rank["media"].apply(cor_sla)
    
            fig_sla = go.Figure(go.Bar(
                x=sla_rank["media"], y=sla_rank["Corretor"],
                orientation="h", text=sla_rank["label"], textposition="outside",
                marker_color=sla_rank["cor"].tolist(),
            ))
            fig_sla.update_layout(
                xaxis_title="Horas", margin=dict(l=0, r=60, t=0, b=0),
                height=max(250, len(sla_rank) * 35), yaxis=dict(autorange="reversed"),
            )
            st.plotly_chart(fig_sla, use_container_width=True)
        else:
            st.info("Sem dados de SLA para este período.")
    
    with col_acao:
        st.subheader("Tempo Médio — 1ª Ação por Corretor")
    
        if "acao_horas" in leads_f.columns:
            acao_rank = (
                leads_f[leads_f["acao_horas"].notna() & leads_f["initial_owner"].notna()]
                .groupby("initial_owner")["acao_horas"]
                .mean()
                .reset_index()
                .rename(columns={"initial_owner": "Corretor", "acao_horas": "media"})
                .sort_values("media")
            )
    
            if not acao_rank.empty:
                acao_rank["label"] = acao_rank["media"].apply(fmt_sla)
                acao_rank["cor"]   = acao_rank["media"].apply(cor_sla)
    
                fig_acao = go.Figure(go.Bar(
                    x=acao_rank["media"], y=acao_rank["Corretor"],
                    orientation="h", text=acao_rank["label"], textposition="outside",
                    marker_color=acao_rank["cor"].tolist(),
                ))
                fig_acao.update_layout(
                    xaxis_title="Horas", margin=dict(l=0, r=60, t=0, b=0),
                    height=max(250, len(acao_rank) * 35), yaxis=dict(autorange="reversed"),
                )
                st.plotly_chart(fig_acao, use_container_width=True)
            else:
                st.info("Sem dados de 1ª ação para este período.")
        else:
            st.info("Coluna 'Data Primeira Ação' não encontrada na planilha.")
    
    st.divider()
    
    # ── Ranking Fechamentos + Ticket Médio ────────────────────────────────────────
    col_rank, col_ticket = st.columns(2)
    
    with col_rank:
        st.subheader("Ranking de Fechamentos")
    
        if not ganhas_f.empty:
            rank = (
                ganhas_f.groupby("corretor")
                .agg(vendas=("valor", "count"), vgv=("valor", "sum"))
                .reset_index()
                .sort_values("vgv", ascending=False)
            )
            rank["vgv_fmt"] = rank["vgv"].apply(fmt_brl)
    
            fig_rank = go.Figure(go.Bar(
                x=rank["vgv"], y=rank["corretor"],
                orientation="h", text=rank["vgv_fmt"], textposition="outside",
                marker_color=COR_PRINCIPAL,
            ))
            fig_rank.update_layout(
                xaxis_title="VGV (R$)", margin=dict(l=0, r=90, t=0, b=0),
                height=max(250, len(rank) * 35), yaxis=dict(autorange="reversed"),
            )
            st.plotly_chart(fig_rank, use_container_width=True)
        else:
            st.info("Sem fechamentos de venda neste período.")
    
    with col_ticket:
        st.subheader("Ticket Médio por Corretor")
    
        if not ganhas_f.empty and "corretor" in ganhas_f.columns:
            ticket_rank = (
                ganhas_f.groupby("corretor")["valor"]
                .mean()
                .reset_index()
                .rename(columns={"valor": "ticket"})
                .sort_values("ticket", ascending=False)
            )
            ticket_rank["label"] = ticket_rank["ticket"].apply(fmt_brl)
    
            fig_ticket = go.Figure(go.Bar(
                x=ticket_rank["ticket"], y=ticket_rank["corretor"],
                orientation="h", text=ticket_rank["label"], textposition="outside",
                marker_color=COR_AMARELO,
            ))
            fig_ticket.update_layout(
                xaxis_title="Ticket Médio (R$)", margin=dict(l=0, r=90, t=0, b=0),
                height=max(250, len(ticket_rank) * 35), yaxis=dict(autorange="reversed"),
            )
            st.plotly_chart(fig_ticket, use_container_width=True)
        else:
            st.info("Sem dados de ticket médio para este período.")
    
    st.divider()
    
    # ── Ciclo de Venda + Motivos de Perda ─────────────────────────────────────────
    col_ciclo, col_perda = st.columns(2)
    
    with col_ciclo:
        st.subheader("Ciclo Médio de Venda por Corretor")
    
        if "ciclo_dias" in leads_f.columns and "final_owner" in leads_f.columns:
            ciclo_rank = (
                leads_f[leads_f["ciclo_dias"].notna() & leads_f["final_owner"].notna()]
                .groupby("final_owner")["ciclo_dias"]
                .mean()
                .reset_index()
                .rename(columns={"final_owner": "Corretor", "ciclo_dias": "ciclo"})
                .sort_values("ciclo")
            )
    
            if not ciclo_rank.empty:
                ciclo_rank["label"] = ciclo_rank["ciclo"].apply(fmt_dias)
    
                fig_ciclo = go.Figure(go.Bar(
                    x=ciclo_rank["ciclo"], y=ciclo_rank["Corretor"],
                    orientation="h", text=ciclo_rank["label"], textposition="outside",
                    marker_color=COR_PRINCIPAL,
                ))
                fig_ciclo.update_layout(
                    xaxis_title="Dias", margin=dict(l=0, r=80, t=0, b=0),
                    height=max(250, len(ciclo_rank) * 35), yaxis=dict(autorange="reversed"),
                )
                st.plotly_chart(fig_ciclo, use_container_width=True)
            else:
                st.info("Sem dados de ciclo de venda para este período.")
        else:
            st.info("Colunas necessárias não encontradas na planilha.")
    
    with col_perda:
        st.subheader("Distribuição de Motivos de Perda")
    
        if "loss_reason" in leads_f.columns:
            motivos = (
                leads_f[leads_f["status"] == "Perdido"]["loss_reason"]
                .replace("", pd.NA)
                .dropna()
                .value_counts()
                .reset_index()
            )
            motivos.columns = ["Motivo", "Quantidade"]
    
            if not motivos.empty:
                fig_perda = go.Figure(go.Bar(
                    x=motivos["Quantidade"], y=motivos["Motivo"],
                    orientation="h", text=motivos["Quantidade"], textposition="outside",
                    marker_color=COR_VERMELHO,
                ))
                fig_perda.update_layout(
                    xaxis_title="Quantidade", margin=dict(l=0, r=40, t=0, b=0),
                    height=max(250, len(motivos) * 35), yaxis=dict(autorange="reversed"),
                )
                st.plotly_chart(fig_perda, use_container_width=True)
            else:
                st.info("Sem motivos de perda registrados neste período.")
        else:
            st.info("Coluna 'Motivo Perda' não encontrada na planilha.")
    
    st.divider()
    
    # ── Leads por Fonte ───────────────────────────────────────────────────────────
    st.subheader("Leads por Fonte de Origem")
    
    if "source" in leads_f.columns:
        fontes = (
            leads_f["source"]
            .replace("", pd.NA)
            .dropna()
            .value_counts()
            .reset_index()
        )
        fontes.columns = ["Fonte", "Leads"]
    
        if not fontes.empty:
            fig_fonte = px.bar(
                fontes.head(10), x="Leads", y="Fonte",
                orientation="h",
                color_discrete_sequence=[COR_PRINCIPAL],
                text="Leads",
            )
            fig_fonte.update_layout(
                margin=dict(l=0, r=0, t=0, b=0),
                height=350,
                yaxis=dict(autorange="reversed"),
            )
            st.plotly_chart(fig_fonte, use_container_width=True)
    


# ─────────────────────────────────────────────────────────────────
# FINANCEIRO
# ─────────────────────────────────────────────────────────────────
VGV_GATILHO_PRIME    = Decimal("2100000")
VENDAS_GATILHO_PRIME = 3

FIN_COR_PRIME3        = "#F59E0B"
FIN_COR_PRIME2        = "#22C55E"
FIN_COR_PRIME1        = "#34D399"
FIN_COR_PRIME_INICIAL = "#06B6D4"
FIN_COR_BASE          = "#6B7280"
FIN_COR_AZUL          = "#1E6FE8"

FIN_ORDEM_PRIME = {"Prime +3": 0, "Prime +2": 1, "Prime +1": 2, "Prime": 3, "Prime Inicial": 4}

FIN_BADGE_PRIME = {
    "Prime +3":      "Prime +3",
    "Prime +2":      "Prime +2",
    "Prime +1":      "Prime +1",
    "Prime":         "Prime",
    "Prime Inicial": "Prime Inicial",
}

FIN_COR_POR_NIVEL = {
    "Prime +3":      FIN_COR_PRIME3,
    "Prime +2":      FIN_COR_PRIME2,
    "Prime +1":      FIN_COR_PRIME1,
    "Prime":         FIN_COR_PRIME_INICIAL,
    "Prime Inicial": FIN_COR_BASE,
}

def fin_parse_brl(val) -> Optional[Decimal]:
    s = str(val).strip()
    if not s:
        return None
    s = s.replace("R$", "").replace(".", "").replace(",", ".").strip()
    try:
        d = Decimal(s)
        return d if d != 0 else None
    except InvalidOperation:
        return None


def fin_fmt_brl(v) -> str:
    if v is None:
        return "—"
    try:
        f = float(v)
    except (TypeError, ValueError):
        return "—"
    return f"R$ {f:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def fin_fmt_pct(v, decimals=1) -> str:
    if v is None:
        return "—"
    return f"{float(v):.{decimals}f}%"


def fin_normalizar_tipo(val: str) -> str:
    s = val.lower().strip()
    if any(k in s for k in ("novo", "lança", "lanca", "planta", "constru")):
        return "Novo"
    if any(k in s for k in ("usado", "revendas", "revenda", "segunda")):
        return "Usado"
    return val.title() if val else ""


def fin_classificar_nivel(num_vendas: int, atingiu_prime: bool) -> str:
    if not atingiu_prime:
        return "Prime Inicial"
    extras = num_vendas - VENDAS_GATILHO_PRIME
    if extras <= 0:
        return "Prime"
    elif extras == 1:
        return "Prime +1"
    elif extras == 2:
        return "Prime +2"
    else:
        return "Prime +3"


@st.cache_data(ttl=300, show_spinner=False)
def fin_carregar_dados():
    sh = _gsheets.get_spreadsheet()

    rows    = sh.worksheet("OP GANHAS").get_all_records()
    ph_rows = sh.worksheet("PRIME HERDADO").get_all_records()

    prime_herdado_set = {
        (str(r.get("Corretor Prime", "")).strip(), str(r.get("Trimestre", "")).strip())
        for r in ph_rows
        if r.get("Corretor Prime") and r.get("Trimestre")
    }

    _MESES = ["Jan","Fev","Mar","Abr","Mai","Jun","Jul","Ago","Set","Out","Nov","Dez"]

    registros = []
    for row in rows:
        corretor  = str(row.get("Responsavel", "")).strip()
        captador  = str(row.get("Captador", "")).strip() or None
        trimestre = str(row.get("TRIMESTRE", "")).strip()
        tipo      = str(row.get("Tipo de Negocio", "")).strip()

        if not corretor or not trimestre:
            continue

        valor          = fin_parse_brl(row.get("Valor ", row.get("Valor", "")))
        comissao_total = fin_parse_brl(row.get("Comissao Total", ""))
        r_corretor     = fin_parse_brl(row.get("R$ Corretor", ""))
        r_captador     = fin_parse_brl(row.get("R$ Captador", ""))
        r_gestao   = fin_parse_brl(row.get("R$ dayvson coord", ""))
        vgv_acum       = fin_parse_brl(row.get("VGV Acumulado", ""))
        categoria      = str(row.get("Categoria Venda", "")).strip()
        prime_flag     = str(row.get("Prime Herdado", "")).strip().upper()
        tipo_imovel    = fin_normalizar_tipo(str(row.get("Tipo de Imovel", row.get("Tipo", ""))).strip())
        regiao         = str(row.get("Regiao", "")).strip().title()

        mes_raw = str(row.get("MES", "")).strip()
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
            "tipo_imovel":    tipo_imovel,
            "valor":          valor,
            "comissao_total": comissao_total,
            "r_corretor":     r_corretor,
            "r_captador":     r_captador,
            "r_gestao":       r_gestao,
            "vgv_acumulado":  vgv_acum,
            "categoria":      categoria,
            "prime_flag":     prime_flag,
            "regiao":         regiao,
        })

    return pd.DataFrame(registros), prime_herdado_set


def fin_agregar_corretores(df: pd.DataFrame, prime_herdado_set: set) -> list[dict]:
    # Mapeamento direto da coluna Categoria Venda → nível exibido
    _CAT_TO_NIVEL = {
        "prime":   "Prime",
        "prime+1": "Prime +1",
        "prime+2": "Prime +2",
        "prime+3": "Prime +3",
    }
    _CAT_ORDEM = list(_CAT_TO_NIVEL.keys())

    # Normalizar nomes para lookup case-insensitive
    prime_herdado_norm = {(n.lower(), t) for (n, t) in prime_herdado_set}

    resultados = []
    corretores_vistos = set()  # nomes em lowercase

    for corretor in sorted(df["corretor"].unique()):
        df_c      = df[df["corretor"] == corretor]
        df_vendas = df_c[df_c["tipo"].str.lower().str.strip() == "venda"]
        df_loc    = df_c[df_c["tipo"].str.lower().str.strip().str.contains("loca", na=False)]

        num_vendas   = len(df_vendas)
        num_locacoes = len(df_loc)

        vgv_vals = df_vendas["vgv_acumulado"].dropna()
        vgv = vgv_vals.max() if not vgv_vals.empty else Decimal("0")

        trimestre_check = df_c["trimestre"].dropna().mode()
        trimestre_check = trimestre_check.iloc[0] if not trimestre_check.empty else ""
        is_prime_herdado = (corretor.lower(), trimestre_check) in prime_herdado_norm

        cats_low = [str(c).strip().lower() for c in df_c["categoria"].values]
        atingiu_prime = (
            any(c in _CAT_TO_NIVEL for c in cats_low)
            or "SIM" in df_c["prime_flag"].values
            or is_prime_herdado
        )

        if atingiu_prime:
            # Usa a coluna Categoria Venda como fonte de verdade para o nível
            prime_cats = [c for c in cats_low if c in _CAT_TO_NIVEL]
            if prime_cats:
                cat_max = max(prime_cats, key=lambda c: _CAT_ORDEM.index(c))
                nivel = _CAT_TO_NIVEL[cat_max]
            else:
                nivel = "Prime"
        else:
            nivel = "Prime Inicial"

        r_corretor_total = df_c["r_corretor"].dropna().sum() or None
        r_gestao_total   = df_c["r_gestao"].dropna().sum() or None
        comissao_agencia = df_c["comissao_total"].dropna().sum() or None

        prog_vgv  = float(min(vgv / VGV_GATILHO_PRIME, Decimal("1"))) if vgv else 0.0
        prog_vend = min(num_vendas / VENDAS_GATILHO_PRIME, 1.0)
        progresso = max(prog_vgv, prog_vend)

        corretores_vistos.add(corretor.lower())
        resultados.append({
            "corretor":         corretor,
            "nivel":            nivel,
            "is_prime_herdado": is_prime_herdado,
            "num_vendas":       num_vendas,
            "num_locacoes":     num_locacoes,
            "vgv":              vgv,
            "comissao_agencia": comissao_agencia,
            "r_corretor":       r_corretor_total,
            "r_gestao":         r_gestao_total,
            "progresso":        progresso,
        })

    # Adicionar corretores com Prime Herdado que não têm vendas no período atual
    trimestres_no_df = set(df["trimestre"].dropna().unique())
    for (nome, trim) in prime_herdado_set:
        if trim not in trimestres_no_df:
            continue
        if nome.lower() in corretores_vistos:
            continue
        resultados.append({
            "corretor":         nome,
            "nivel":            "Prime",
            "is_prime_herdado": True,
            "num_vendas":       0,
            "num_locacoes":     0,
            "vgv":              Decimal("0"),
            "comissao_agencia": None,
            "r_corretor":       None,
            "r_gestao":         None,
            "progresso":        1.0,
        })

    resultados.sort(key=lambda x: (
        FIN_ORDEM_PRIME.get(x["nivel"], 99),
        -(float(x["r_corretor"] or 0)),
    ))
    return resultados


FIN_NIVEIS_ORDEM = ["Prime +3", "Prime +2", "Prime +1", "Prime", "Prime Inicial"]

with tab2:

    st.title("Dashboard Financeiro")

    fin_df, fin_prime_herdado_set = fin_carregar_dados()

    fin_trimestres = sorted(fin_df["trimestre"].dropna().replace("", pd.NA).dropna().unique(), reverse=True)
    if not fin_trimestres:
        st.error("Nenhuma venda encontrada na planilha.")
        st.stop()

    fin_meses_ord = (
        fin_df[fin_df["mes_key"] != ""][["mes_key", "mes_label"]]
        .drop_duplicates()
        .sort_values("mes_key", ascending=False)
    )
    fin_meses_keys   = fin_meses_ord["mes_key"].tolist()
    fin_meses_labels = fin_meses_ord["mes_label"].tolist()

    # ── Filtro de período ─────────────────────────────────────────────────────
    fin_regioes_disp = (
        sorted(fin_df["regiao"].dropna().replace("", pd.NA).dropna().unique().tolist(), key=str)
        if "regiao" in fin_df.columns else []
    )

    col_f1, col_f2, col_f3, col_f4 = st.columns([2, 3, 2, 2])
    with col_f1:
        fin_tipo_periodo = st.selectbox("Período", ["Todos", "Trimestre", "Mês"], key="fin_periodo")
    with col_f2:
        if fin_tipo_periodo == "Trimestre":
            fin_periodo_val = st.selectbox("Trimestre", fin_trimestres, key="fin_trimestre")
            fin_periodo_key = None
        elif fin_tipo_periodo == "Mês":
            fin_idx = st.selectbox("Mês", range(len(fin_meses_labels)), key="fin_mes",
                                   format_func=lambda i: fin_meses_labels[i])
            fin_periodo_key = fin_meses_keys[fin_idx]
            fin_periodo_val = None
        else:
            fin_periodo_val = None
            fin_periodo_key = None
    with col_f3:
        fin_regiao_sel = st.multiselect("Região", fin_regioes_disp, placeholder="Todas", key="fin_regiao")
    with col_f4:
        fin_tipo_imovel_sel = st.selectbox("Tipo de Imóvel", ["Todos", "Novo", "Usado"], key="fin_tipo_imovel")

    if fin_tipo_periodo == "Trimestre":
        fin_df_fil = fin_df[fin_df["trimestre"] == fin_periodo_val].copy()
    elif fin_tipo_periodo == "Mês":
        fin_df_fil = fin_df[fin_df["mes_key"] == fin_periodo_key].copy()
    else:
        fin_df_fil = fin_df.copy()

    if fin_regiao_sel and "regiao" in fin_df_fil.columns:
        fin_df_fil = fin_df_fil[fin_df_fil["regiao"].isin(fin_regiao_sel)]

    if fin_tipo_imovel_sel != "Todos" and "tipo_imovel" in fin_df_fil.columns:
        fin_df_fil = fin_df_fil[fin_df_fil["tipo_imovel"] == fin_tipo_imovel_sel]

    fin_df_vendas_fil = fin_df_fil[fin_df_fil["tipo"].str.lower().str.strip() == "venda"]
    fin_df_loc_fil    = fin_df_fil[fin_df_fil["tipo"].str.lower().str.strip().str.contains("loca", na=False)]
    fin_resultados_todos = fin_agregar_corretores(fin_df_fil, fin_prime_herdado_set)

    # ══════════════════════════════════════════════════════════════════════════
    # SEÇÃO 1 — GESTÃO
    # ══════════════════════════════════════════════════════════════════════════
    st.markdown(
        "<div class='ol-section'>"
        "<p class='ol-section-title' style='color:#184D6C;'>Gestão</p>"
        "</div>",
        unsafe_allow_html=True,
    )

    fin_total_vendas   = len(fin_df_vendas_fil)
    fin_total_locacoes = len(fin_df_loc_fil)
    fin_total_negocios = fin_total_vendas + fin_total_locacoes
    fin_total_vgv      = sum(float(r["vgv"] or 0) for r in fin_resultados_todos)
    fin_ticket_medio   = fin_total_vgv / fin_total_vendas if fin_total_vendas > 0 else None

    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("VGV do Período",    fin_fmt_brl(fin_total_vgv))
    k2.metric("Ticket Médio",      fin_fmt_brl(fin_ticket_medio))
    k3.metric("Negócios Fechados", f"{fin_total_negocios:,}")
    k4.metric("Vendas",            f"{fin_total_vendas:,}")
    k5.metric("Locações",          f"{fin_total_locacoes:,}")

    fin_total_agencia  = sum(float(r["comissao_agencia"] or 0) for r in fin_resultados_todos)
    fin_total_gestao   = sum(float(r["r_gestao"] or 0) for r in fin_resultados_todos)
    fin_total_corretor = sum(float(r["r_corretor"] or 0) for r in fin_resultados_todos)
    fin_total_captacao = sum(float(v) for v in fin_df_fil["r_captador"].dropna())
    fin_n_prime        = sum(1 for r in fin_resultados_todos if r["nivel"] != "Prime Inicial")
    fin_n_base         = sum(1 for r in fin_resultados_todos if r["nivel"] == "Prime Inicial")

    if fin_total_agencia > 0:
        fin_liquido     = fin_total_agencia - fin_total_corretor - fin_total_gestao - fin_total_captacao
        fin_pct_liquido = fin_liquido / fin_total_agencia * 100
    else:
        fin_liquido     = 0.0
        fin_pct_liquido = None

    k6, k7, k8, k9, k10, k10b = st.columns(6)
    k6.metric("Comissão Imobiliária",  fin_fmt_brl(fin_total_agencia))
    k7.metric("Total Pago Corretores", fin_fmt_brl(fin_total_corretor))
    k8.metric("Total Pago à Gestão",   fin_fmt_brl(fin_total_gestao))
    k9.metric("Total Pago à Captação", fin_fmt_brl(fin_total_captacao if fin_total_captacao > 0 else None))
    k10.metric("% Líquido da Imob.",   fin_fmt_pct(fin_pct_liquido),
               help="(Comissão − Corretores − Gestão − Captação) ÷ Comissão")
    k10b.metric("R$ Líquido Imob.",    fin_fmt_brl(fin_liquido if fin_total_agencia > 0 else None))

    k11, *_ = st.columns(5)
    k11.metric("Prime", fin_n_prime)

    st.divider()

    # ── Gráficos de gestão ────────────────────────────────────────────────────
    col_vgv_rank, _ = st.columns(2)

    with col_vgv_rank:
        st.subheader("Ranking VGV por Corretor")
        fin_vgv_data = sorted(
            [(r["corretor"], float(r["vgv"] or 0), r["nivel"]) for r in fin_resultados_todos],
            key=lambda x: x[1], reverse=True,
        )
        if fin_vgv_data:
            fig_vgv = go.Figure(go.Bar(
                x=[d[1] for d in fin_vgv_data], y=[d[0] for d in fin_vgv_data],
                orientation="h",
                text=[fin_fmt_brl(Decimal(str(d[1]))) for d in fin_vgv_data],
                textposition="outside",
                marker_color=[FIN_COR_POR_NIVEL.get(d[2], FIN_COR_BASE) for d in fin_vgv_data],
            ))
            fig_vgv.add_vline(x=float(VGV_GATILHO_PRIME), line_dash="dash",
                              line_color=FIN_COR_PRIME2,
                              annotation_text="Meta Prime (R$ 2,1M)",
                              annotation_position="top right",
                              annotation_font_color=FIN_COR_PRIME2)
            fig_vgv.update_layout(margin=dict(l=0,r=100,t=10,b=0),
                                  height=max(280, len(fin_vgv_data)*42),
                                  xaxis_title="VGV (R$)",
                                  yaxis=dict(autorange="reversed"))
            st.plotly_chart(fig_vgv, use_container_width=True)
        else:
            st.info("Sem dados de VGV para este período.")

    col_nv_rank, col_com_rank = st.columns(2)

    with col_nv_rank:
        st.subheader("Ranking — Nº de Vendas por Corretor")
        fin_vendas_sorted = sorted(fin_resultados_todos, key=lambda x: x["num_vendas"], reverse=True)
        if fin_vendas_sorted:
            fig_nv = go.Figure(go.Bar(
                x=[r["num_vendas"] for r in fin_vendas_sorted],
                y=[r["corretor"] for r in fin_vendas_sorted],
                orientation="h",
                text=[r["num_vendas"] for r in fin_vendas_sorted],
                textposition="outside",
                marker_color=[FIN_COR_POR_NIVEL.get(r["nivel"], FIN_COR_BASE) for r in fin_vendas_sorted],
            ))
            fig_nv.update_layout(margin=dict(l=0,r=40,t=10,b=0),
                                 height=max(250, len(fin_vendas_sorted)*42),
                                 xaxis_title="Número de Vendas",
                                 yaxis=dict(autorange="reversed"))
            st.plotly_chart(fig_nv, use_container_width=True)

    with col_com_rank:
        st.subheader("Ranking — Comissão Gerada por Corretor")
        st.caption("Valor total a receber por corretor no período")
        fin_com_sorted = sorted(
            [(r["corretor"], float(r["r_corretor"] or 0), r["nivel"]) for r in fin_resultados_todos],
            key=lambda x: x[1], reverse=True,
        )
        if fin_com_sorted:
            fig_com = go.Figure(go.Bar(
                x=[d[1] for d in fin_com_sorted],
                y=[d[0] for d in fin_com_sorted],
                orientation="h",
                text=[fin_fmt_brl(Decimal(str(d[1]))) for d in fin_com_sorted],
                textposition="outside",
                marker_color=[FIN_COR_POR_NIVEL.get(d[2], FIN_COR_BASE) for d in fin_com_sorted],
            ))
            fig_com.update_layout(margin=dict(l=0,r=100,t=10,b=0),
                                  height=max(250, len(fin_com_sorted)*42),
                                  xaxis_title="Comissão (R$)",
                                  yaxis=dict(autorange="reversed"))
            st.plotly_chart(fig_com, use_container_width=True)
        else:
            st.info("Sem dados de comissão para este período.")

    col_cap_rank, _ = st.columns(2)

    with col_cap_rank:
        st.subheader("Ranking de Captadores")
        fin_df_cap = fin_df_vendas_fil[
            fin_df_vendas_fil["captador"].notna() &
            (fin_df_vendas_fil["captador"] != "")
        ].copy()
        if not fin_df_cap.empty:
            fin_df_cap["valor_num"] = fin_df_cap["valor"].apply(
                lambda v: float(v) if v is not None else 0.0
            )
            fin_cap_rank = (
                fin_df_cap.groupby("captador")
                .agg(vendas=("valor_num","count"), vgv=("valor_num","sum"))
                .reset_index().sort_values("vgv", ascending=False)
            )
            fin_cap_rank["vgv_fmt"] = fin_cap_rank["vgv"].apply(
                lambda v: fin_fmt_brl(Decimal(str(v))) if v else "—"
            )
            fig_cap = go.Figure(go.Bar(
                x=fin_cap_rank["vgv"].tolist(), y=fin_cap_rank["captador"].tolist(),
                orientation="h", text=fin_cap_rank["vgv_fmt"].tolist(),
                textposition="outside", marker_color=FIN_COR_AZUL,
                customdata=fin_cap_rank["vendas"].tolist(),
                hovertemplate="<b>%{y}</b><br>VGV: %{text}<br>Vendas: %{customdata}<extra></extra>",
            ))
            fig_cap.update_layout(margin=dict(l=0,r=100,t=10,b=0),
                                  height=max(250, len(fin_cap_rank)*42),
                                  xaxis_title="VGV (R$)",
                                  yaxis=dict(autorange="reversed"))
            st.plotly_chart(fig_cap, use_container_width=True)
        else:
            st.info("Sem dados de captador para este período.")

    # ── Novo x Usado ──────────────────────────────────────────────────────────
    col_pizza, _ = st.columns(2)
    with col_pizza:
        st.subheader("Tipo de Imóvel — Novo x Usado")
        fin_tipo_counts = (
            fin_df_vendas_fil["tipo_imovel"]
            .replace("", pd.NA).dropna()
            .value_counts().reset_index()
        )
        fin_tipo_counts.columns = ["Tipo", "Qtd"]

        if not fin_tipo_counts.empty:
            fig_pizza = go.Figure(go.Pie(
                labels=fin_tipo_counts["Tipo"], values=fin_tipo_counts["Qtd"],
                hole=0.45, textinfo="label+percent+value",
                marker_colors=[FIN_COR_AZUL, FIN_COR_PRIME2, FIN_COR_PRIME3],
            ))
            fig_pizza.update_layout(margin=dict(l=0,r=0,t=0,b=20), height=320,
                                    legend=dict(orientation="h", y=-0.1))
            st.plotly_chart(fig_pizza, use_container_width=True)
        else:
            st.info("Sem dados de tipo de imóvel para este período.")

    # ══════════════════════════════════════════════════════════════════════════
    # SEÇÃO 2 — CORRETORES
    # ══════════════════════════════════════════════════════════════════════════
    st.markdown(
        "<div class='ol-section'>"
        "<p class='ol-section-title' style='color:#184D6C;'>Corretores</p>"
        "<p class='ol-section-sub' style='color:#184D6C;'>Desempenho individual por período</p>"
        "</div>",
        unsafe_allow_html=True,
    )

    fin_corretores_disp = sorted(fin_df["corretor"].dropna().replace("", pd.NA).dropna().unique().tolist(), key=str)
    fin_corretor_sel = st.multiselect("Filtrar por corretor", fin_corretores_disp,
                                      placeholder="Todos os corretores", key="fin_corretor")

    if fin_corretor_sel:
        fin_df_cor = fin_df_fil[fin_df_fil["corretor"].isin(fin_corretor_sel)].copy()
    else:
        fin_df_cor = fin_df_fil.copy()

    fin_resultados_cor = fin_agregar_corretores(fin_df_cor, fin_prime_herdado_set)

    fin_cor_vgv    = sum(float(r["vgv"] or 0) for r in fin_resultados_cor)
    fin_cor_vendas = sum(r["num_vendas"] for r in fin_resultados_cor)
    fin_cor_loc    = sum(r["num_locacoes"] for r in fin_resultados_cor)
    fin_cor_ticket = fin_cor_vgv / fin_cor_vendas if fin_cor_vendas > 0 else None
    fin_cor_com    = sum(float(r["r_corretor"] or 0) for r in fin_resultados_cor)

    kc1, kc2, kc3, kc4 = st.columns(4)
    kc1.metric("VGV",             fin_fmt_brl(fin_cor_vgv))
    kc2.metric("Ticket Médio",    fin_fmt_brl(fin_cor_ticket))
    kc3.metric("Negócios",        f"{fin_cor_vendas + fin_cor_loc:,}")
    kc4.metric("Comissão Gerada", fin_fmt_brl(fin_cor_com))

    st.divider()

    for nivel in FIN_NIVEIS_ORDEM:
        grupo = [r for r in fin_resultados_cor if r["nivel"] == nivel]
        if not grupo:
            continue

        fin_nivel_cor   = FIN_COR_POR_NIVEL.get(nivel, FIN_COR_BASE)
        fin_badge_label = FIN_BADGE_PRIME.get(nivel, nivel)
        st.markdown(
            f"<span style='display:inline-block;width:8px;height:8px;border-radius:50%;"
            f"background:{fin_nivel_cor};margin-right:7px;vertical-align:middle;'></span>"
            f"<strong style='font-family:TrajanPro,serif;letter-spacing:.07em;"
            f"font-size:.78rem;text-transform:uppercase;color:{fin_nivel_cor};'>{fin_badge_label}</strong>",
            unsafe_allow_html=True,
        )

        for r in grupo:
            herdado_suffix = " — Herdado" if r["is_prime_herdado"] and nivel != "Prime Inicial" else ""

            with st.container(border=True):
                col_nome, col_vendas, col_loc, col_vgv = st.columns([3, 1, 1, 2])
                with col_nome:
                    st.markdown(f"**{r['corretor']}**")
                col_vendas.metric("Vendas",   r["num_vendas"])
                col_loc.metric("Locações",    r["num_locacoes"])
                col_vgv.metric("VGV",         fin_fmt_brl(r["vgv"]))

            if nivel == "Prime Inicial":
                vgv_f     = float(r["vgv"] or 0)
                falta_vgv = max(float(VGV_GATILHO_PRIME) - vgv_f, 0)
                falta_v   = max(VENDAS_GATILHO_PRIME - r["num_vendas"], 0)
                msg = (
                    f"Faltam {fin_fmt_brl(falta_vgv)} em VGV  ou  {falta_v} venda(s) para Prime"
                    if falta_vgv > 0 and falta_v > 0
                    else "Atingiu o gatilho — aguardando confirmação Prime"
                )
                st.progress(r["progresso"], text=f"Progresso para Prime — {msg}")

        st.markdown("")



# ─────────────────────────────────────────────────────────────────
# INSTITUCIONAL
# ─────────────────────────────────────────────────────────────────
COR_QUENTE = '#EF4444'
COR_LIXO   = '#9CA3AF'

def qualificar(row) -> str:
    if row.get("status", "") == "Perdido":
        return "Descartados"
    return "Quente"


@st.cache_data(ttl=300, show_spinner=False)
def ins_carregar_dados():
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
    df["trimestre"]  = df["created_at"].apply(trimestre_de_dt)
    df["mes_key"]    = df["created_at"].apply(mes_key)
    df["mes_label"]  = df["created_at"].apply(mes_label)
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



with tab3:
    
    # ── Interface ────────────────────────────────────────────────────────────────
    st.title("Relatório de Campanhas")
    
    df = ins_carregar_dados()
    
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
        sorted(df["source"].dropna().replace("", pd.NA).dropna().unique().tolist(), key=str)
        if "source" in df.columns else []
    )
    
    col_f1, col_f2, col_f3 = st.columns([2, 2, 3])
    
    with col_f1:
        tipo_periodo = st.selectbox("Período", ["Todos", "Trimestre", "Mês"], key="ins_per_odo")
    
    with col_f2:
        if tipo_periodo == "Trimestre":
            trimestre_sel = st.selectbox("Trimestre", trimestres_disp, key="ins_trimestre")
            mes_sel_key = None
        elif tipo_periodo == "Mês":
            idx = st.selectbox("Mês", range(len(meses_labels)), key="ins_m_s",
                               format_func=lambda i: meses_labels[i])
            mes_sel_key   = meses_keys[idx]
            trimestre_sel = None
        else:
            trimestre_sel = None
            mes_sel_key   = None
    
    with col_f3:
        campanha_sel = st.multiselect("Campanha", campanhas_disp, placeholder="Todas", key="ins_campanha")
    
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
    k2.metric("Leads Quentes",           f"{n_quente:,}")
    k3.metric("Descartados",            f"{n_descartados:,}")
    k4.metric("Taxa de Conversão",      f"{taxa_conv:.1f}%")
    
    st.divider()
    
    # ── Qualificação térmica + Volume por campanha ────────────────────────────────
    col_term, col_camp = st.columns([2, 3])
    
    with col_term:
        st.subheader("Qualificação dos Leads")
    
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
    
