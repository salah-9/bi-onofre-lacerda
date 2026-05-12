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

st.set_page_config(
    page_title="BI Onofre Lacerda",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="collapsed",
)

NAVY = "#062b41"
GOLD = "#cfaa52"

st.markdown("""
<style>
[data-testid="stToolbar"] { display: none !important; }
header[data-testid="stHeader"] { display: none !important; }
section[data-testid="stSidebar"] { display: none !important; }
[data-testid="stMetricValue"] { font-size: 1rem !important; white-space: nowrap !important; overflow: hidden !important; text-overflow: ellipsis !important; font-weight: 700; }
[data-testid="stMetricLabel"] { font-size: 0.7rem !important; }
hr { border-color: #cfaa5244 !important; }
</style>
""", unsafe_allow_html=True)

_auth.require_login()

# ── Header ────────────────────────────────────────────────────────────────────
col_logo, _, col_dark = st.columns([3, 3, 1])
with col_logo:
    logo = Path(__file__).parent / "logo_onofre.webp"
    if logo.exists():
        st.image(str(logo), width=160)
    else:
        st.markdown(f"<h2 style='color:{NAVY}; margin:0;'>Onofre Lacerda</h2>", unsafe_allow_html=True)
with col_dark:
    dark = st.toggle("🌙", value=st.session_state.get("dark_mode", False), key="dark_mode")

if dark:
    st.markdown(f"""<style>
    .stApp, .main .block-container {{ background-color: #0d1b2a !important; }}
    h1, h2, h3 {{ color: {GOLD} !important; }}
    p, span, .stMarkdown {{ color: #dde3ec !important; }}
    [data-testid="stMetricValue"] {{ color: {GOLD} !important; }}
    [data-testid="stVerticalBlockBorderWrapper"] > div {{ background-color: #162032 !important; border-color: #2a3a50 !important; }}
    </style>""", unsafe_allow_html=True)
else:
    st.markdown(f"""<style>
    h1, h2, h3 {{ color: {NAVY} !important; }}
    [data-testid="stMetricValue"] {{ color: {NAVY} !important; }}
    </style>""", unsafe_allow_html=True)

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
tab1, tab2, tab3 = st.tabs(["📊  Comercial", "💰  Financeiro", "🏢  Institucional"])

# ─────────────────────────────────────────────────────────────────
# COMERCIAL
# ─────────────────────────────────────────────────────────────────
COR_PRINCIPAL = '#1E6FE8'
COR_VERDE     = '#22C55E'
COR_AMARELO   = '#F59E0B'
COR_VERMELHO  = '#EF4444'
COR_CINZA     = '#6B7280'

@st.cache_data(ttl=300, show_spinner="Carregando dados da planilha...")
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
    }
    leads = leads.rename(columns={k: v for k, v in col_map_leads.items() if k in leads.columns})

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
    }
    ganhas = ganhas.rename(columns={k: v for k, v in col_map_ganhas.items() if k in ganhas.columns})

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
    st.caption("Funil de vendas · SLA de atendimento · Ranking de corretores")
    
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
        leads["initial_owner"].dropna().replace("", pd.NA).dropna().unique().tolist()
    )
    campanhas_disp = (
        sorted(leads["source"].dropna().replace("", pd.NA).dropna().unique().tolist())
        if "source" in leads.columns else []
    )
    
    col_f1, col_f2, col_f3, col_f4 = st.columns([2, 2, 3, 3])
    
    with col_f1:
        tipo_periodo = st.selectbox("Período", ["Todos", "Trimestre", "Mês"])
    
    with col_f2:
        if tipo_periodo == "Trimestre":
            trimestre_sel = st.selectbox("Trimestre", trimestres_disp)
            mes_sel_key = None
        elif tipo_periodo == "Mês":
            mes_idx = st.selectbox("Mês", range(len(meses_labels)),
                                   format_func=lambda i: meses_labels[i])
            mes_sel_key = meses_keys[mes_idx]
            trimestre_sel = None
        else:
            trimestre_sel = None
            mes_sel_key = None
    
    with col_f3:
        corretor_sel = st.multiselect("Corretor", corretores_disp, placeholder="Todos")
    
    with col_f4:
        campanha_sel = st.multiselect("Campanha", campanhas_disp, placeholder="Todas")
    
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
        st.caption(f"Tempo médio do lead gerado ao 1º contato  |  Geral: {fmt_sla(sla_medio)}")
    
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
        st.caption(f"Tempo até a primeira movimentação no funil  |  Geral: {fmt_sla(acao_medio)}")
    
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
        st.caption("VGV acumulado por corretor (locações excluídas)")
    
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
        st.caption("Valor médio dos imóveis negociados — identifica foco em alto padrão vs. volume")
    
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
        st.caption(f"Dias entre geração do lead e fechamento  |  Geral: {fmt_dias(ciclo_medio)}")
    
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
        st.caption("Por que os negócios não fecham")
    
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
    
    st.caption("Dados atualizados a cada 5 min  ·  Planilha: Cópia de OL LEADS GERAIS dash 2")


# ─────────────────────────────────────────────────────────────────
# FINANCEIRO
# ─────────────────────────────────────────────────────────────────
VGV_GATILHO_PRIME = Decimal('2100000')
VENDAS_GATILHO_PRIME = 3
COR_PRIME = '#22C55E'
COR_PRIME_HERDADO = '#8B5CF6'
COR_BASE = '#6B7280'

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
    f = float(v)
    return f"R$ {f:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def fin_fmt_pct(v) -> str:
    if v is None:
        return "—"
    return f"{float(v):.0f}%"


@st.cache_data(ttl=300, show_spinner="Carregando dados da planilha...")
def fin_carregar_dados():
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

        valor         = fin_parse_brl(row.get("Valor ", row.get("Valor", "")))
        comissao_total = fin_parse_brl(row.get("Comissao Total", ""))
        r_corretor    = fin_parse_brl(row.get("R$ Corretor", ""))
        r_captador    = fin_parse_brl(row.get("R$ Captador", ""))
        pct_corretor  = row.get("% Comissão corretor", "")
        vgv_acum      = fin_parse_brl(row.get("VGV Acumulado", ""))
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


def fin_agregar_corretores(df: pd.DataFrame, tipo: str, valor: str, prime_herdado_set: set) -> list[dict]:
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

@st.cache_data(ttl=300, show_spinner="Carregando dados da planilha...")
def fin_carregar_dados():
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

        valor         = fin_parse_brl(row.get("Valor ", row.get("Valor", "")))
        comissao_total = fin_parse_brl(row.get("Comissao Total", ""))
        r_corretor    = fin_parse_brl(row.get("R$ Corretor", ""))
        r_captador    = fin_parse_brl(row.get("R$ Captador", ""))
        pct_corretor  = row.get("% Comissão corretor", "")
        vgv_acum      = fin_parse_brl(row.get("VGV Acumulado", ""))
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


def fin_agregar_corretores(df: pd.DataFrame, tipo: str, valor: str, prime_herdado_set: set) -> list[dict]:
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

with tab2:
    
    st.title("Dashboard Financeiro")
    st.caption("Comissões · Status Base / Prime · Valor a pagar")
    
    df, prime_herdado_set = fin_carregar_dados()
    
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
    
    resultados = fin_agregar_corretores(df_fil, tipo_periodo, periodo_val, prime_herdado_set)
    
    # ── KPIs ──────────────────────────────────────────────────────────────────────
    st.divider()
    
    total_vgv        = sum(float(r["vgv"] or 0) for r in resultados)
    total_agencia    = sum(float(r["comissao_agencia"] or 0) for r in resultados)
    total_corretores = sum(float(r["r_corretor"] or 0) for r in resultados)
    n_prime          = sum(1 for r in resultados if r["status"] in ("Prime", "Prime Herdado"))
    n_base           = sum(1 for r in resultados if r["status"] == "Base")
    
    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("VGV do Período",            fin_fmt_brl(total_vgv))
    k2.metric("Comissão Imobiliária",      fin_fmt_brl(total_agencia))
    k3.metric("Total a Pagar Corretores",  fin_fmt_brl(total_corretores))
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
    
        r_corretor_txt = fin_fmt_brl(r["r_corretor"]) if r["r_corretor"] else "⚠️ Pendente"
        pct_txt        = fin_fmt_pct(r["pct_atual"])  if r["pct_atual"] is not None else "—"
    
        with st.container(border=True):
            col_nome, col_vendas, col_loc, col_vgv, col_imob, col_taxa, col_pagar = st.columns(
                [3, 1, 1, 2, 2, 1, 2]
            )
    
            with col_nome:
                st.markdown(f"**{corretor}**")
                st.caption(BADGE[status])
    
            col_vendas.metric("Vendas",     r["num_vendas"])
            col_loc.metric("Locações",     r["num_locacoes"])
            col_vgv.metric("VGV",         fin_fmt_brl(r["vgv"]))
            col_imob.metric("Com. Imob.", fin_fmt_brl(r["comissao_agencia"]))
            col_taxa.metric("Taxa",        pct_txt)
            col_pagar.metric("A Pagar",   fin_fmt_brl(r["r_corretor"]) if r["r_corretor"] else "⚠️ Pendente")
    
        if status == "Base":
            vgv_f      = float(r["vgv"] or 0)
            falta_vgv  = max(float(VGV_GATILHO_PRIME) - vgv_f, 0)
            falta_vend = max(VENDAS_GATILHO_PRIME - r["num_vendas"], 0)
    
            if falta_vgv > 0 and falta_vend > 0:
                msg = f"Faltam {fin_fmt_brl(falta_vgv)} em VGV  ou  {falta_vend} venda(s) para Prime"
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
    labels = [fin_fmt_brl(r["vgv"]) for r in resultados]
    
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
        labels_c = [fin_fmt_brl(Decimal(str(v))) for v in vals_c]
    
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


# ─────────────────────────────────────────────────────────────────
# INSTITUCIONAL
# ─────────────────────────────────────────────────────────────────
COR_QUENTE = '#EF4444'
COR_LIXO   = '#9CA3AF'

def qualificar(row) -> str:
    if row.get("status", "") == "Perdido":
        return "Descartados"
    return "Quente"


@st.cache_data(ttl=300, show_spinner="Carregando dados...")
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
    st.caption("Volume de oportunidades · Qualificação de leads · Evolução por período")
    
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
