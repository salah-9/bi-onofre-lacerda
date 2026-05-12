"""Dashboard Comercial — Funil de vendas e SLA de atendimento."""

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
import _gsheets

ROOT = Path(__file__).parent.parent
CLIENT_SECRET = ROOT / "client_secret.json"
TOKEN_DIR = ROOT / ".auth"
SPREADSHEET_ID = "1yPE_XlMWbk1di6xK2bD68w5IbZkVi2JqILC0bXwEykc"

st.set_page_config(
    page_title="Dashboard Comercial",
    page_icon="🏠",
    layout="wide",
)


COR_PRINCIPAL = "#1E6FE8"
COR_VERDE     = "#22C55E"
COR_AMARELO   = "#F59E0B"
COR_VERMELHO  = "#EF4444"
COR_CINZA     = "#6B7280"

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


def mes_ano_str(dt: datetime) -> str:
    meses = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun",
             "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
    return f"{meses[dt.month - 1]}/{dt.year}"


def mes_ano_key(dt: datetime) -> str:
    return dt.strftime("%Y-%m")


@st.cache_data(ttl=300, show_spinner="Carregando dados da planilha...")
def carregar_dados():
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
    leads["trimestre"] = leads["created_at"].apply(trimestre)
    leads["mes_key"]   = leads["created_at"].apply(mes_ano_key)
    leads["mes_label"] = leads["created_at"].apply(mes_ano_str)

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
    ganhas["trimestre"] = ganhas["won_at"].apply(trimestre)
    ganhas["mes_key"]   = ganhas["won_at"].apply(mes_ano_key)
    ganhas = ganhas[ganhas["contract_type"].str.lower().str.strip() != "locação"]

    return leads, ganhas


_brand.setup()

# ── Interface ────────────────────────────────────────────────────────────────
st.title("Dashboard Comercial")
st.caption("Funil de vendas · SLA de atendimento · Ranking de corretores")

leads, ganhas = carregar_dados()

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
