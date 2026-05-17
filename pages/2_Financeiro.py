"""Dashboard Financeiro — Gestão e Corretores."""

import sys
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

VGV_GATILHO_PRIME    = Decimal("2100000")
VENDAS_GATILHO_PRIME = 3

st.set_page_config(
    page_title="Dashboard Financeiro",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded",
)

COR_PRIME3        = "#F59E0B"
COR_PRIME2        = "#22C55E"
COR_PRIME1        = "#34D399"
COR_PRIME_INICIAL = "#06B6D4"
COR_BASE          = "#6B7280"
COR_AZUL          = "#1E6FE8"
COR_VERMELHO      = "#EF4444"

NIVEIS_ORDEM = ["Prime +3", "Prime +2", "Prime +1", "Prime inicial", "Base"]

ORDEM_PRIME = {n: i for i, n in enumerate(NIVEIS_ORDEM)}

BADGE_PRIME = {
    "Prime +3":      "🥇 Prime +3",
    "Prime +2":      "🟢 Prime +2",
    "Prime +1":      "🟢 Prime +1",
    "Prime inicial": "🟢 Prime",
    "Base":          "⚪ Base",
}

COR_POR_NIVEL = {
    "Prime +3":      COR_PRIME3,
    "Prime +2":      COR_PRIME2,
    "Prime +1":      COR_PRIME1,
    "Prime inicial": COR_PRIME_INICIAL,
    "Base":          COR_BASE,
}


def classificar_nivel(num_vendas: int, atingiu_prime: bool) -> str:
    if not atingiu_prime:
        return "Base"
    extras = num_vendas - VENDAS_GATILHO_PRIME
    if extras <= 0:
        return "Prime inicial"
    elif extras == 1:
        return "Prime +1"
    elif extras == 2:
        return "Prime +2"
    else:
        return "Prime +3"


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
    try:
        f = float(v)
    except (TypeError, ValueError):
        return "—"
    return f"R$ {f:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def fmt_pct(v, decimals=1) -> str:
    if v is None:
        return "—"
    return f"{float(v):.{decimals}f}%"


@st.cache_data(ttl=300, show_spinner="Carregando dados da planilha...")
def carregar_dados():
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

        valor          = parse_brl(row.get("Valor ", row.get("Valor", "")))
        comissao_total = parse_brl(row.get("Comissao Total", ""))
        r_corretor     = parse_brl(row.get("R$ Corretor", ""))
        r_captador     = parse_brl(row.get("R$ Captador", ""))
        r_gestao       = parse_brl(row.get("R$ Dayvson", ""))
        vgv_acum       = parse_brl(row.get("VGV Acumulado", ""))
        categoria      = str(row.get("Categoria Venda", "")).strip()
        prime_flag     = str(row.get("Prime Herdado", "")).strip().upper()
        tipo_imovel    = str(row.get("Tipo", "")).strip()

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
        })

    return pd.DataFrame(registros), prime_herdado_set


def agregar_corretores(df: pd.DataFrame, prime_herdado_set: set) -> list[dict]:
    resultados = []

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
        is_prime_herdado = (corretor, trimestre_check) in prime_herdado_set
        atingiu_prime = (
            "Prime" in df_c["categoria"].values
            or "SIM" in df_c["prime_flag"].values
            or is_prime_herdado
        )

        nivel = classificar_nivel(num_vendas, atingiu_prime)

        r_corretor_total = df_c["r_corretor"].dropna().sum() or None
        r_gestao_total   = df_c["r_gestao"].dropna().sum() or None
        comissao_agencia = df_c["comissao_total"].dropna().sum() or None

        prog_vgv  = float(min(vgv / VGV_GATILHO_PRIME, Decimal("1"))) if vgv else 0.0
        prog_vend = min(num_vendas / VENDAS_GATILHO_PRIME, 1.0)
        progresso = max(prog_vgv, prog_vend)

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

    resultados.sort(key=lambda x: (
        ORDEM_PRIME.get(x["nivel"], 99),
        -(float(x["r_corretor"] or 0)),
    ))
    return resultados


# ── Auth + Brand ──────────────────────────────────────────────────────────────
_auth.require_login()
_brand.setup()

st.title("Dashboard Financeiro")
st.caption("Visão de gestão e desempenho dos corretores")

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

# ── Filtros globais de período ────────────────────────────────────────────────
col_f1, col_f2 = st.columns([2, 3])

with col_f1:
    tipo_periodo = st.selectbox("Período", ["Todos", "Trimestre", "Mês"])

with col_f2:
    if tipo_periodo == "Trimestre":
        periodo_val = st.selectbox("Trimestre", trimestres)
        periodo_key = None
    elif tipo_periodo == "Mês":
        idx = st.selectbox("Mês", range(len(meses_labels)), format_func=lambda i: meses_labels[i])
        periodo_key = meses_keys[idx]
        periodo_val = None
    else:
        periodo_val = None
        periodo_key = None

# Aplica filtro de período
if tipo_periodo == "Trimestre":
    df_fil = df[df["trimestre"] == periodo_val].copy()
elif tipo_periodo == "Mês":
    df_fil = df[df["mes_key"] == periodo_key].copy()
else:
    df_fil = df.copy()

df_vendas_fil = df_fil[df_fil["tipo"].str.lower().str.strip() == "venda"]
df_loc_fil    = df_fil[df_fil["tipo"].str.lower().str.strip().str.contains("loca", na=False)]

resultados_todos = agregar_corretores(df_fil, prime_herdado_set)

# ══════════════════════════════════════════════════════════════════════════════
# SEÇÃO 1 — GESTÃO
# ══════════════════════════════════════════════════════════════════════════════
st.markdown(
    "<h2 style='margin-top:1.5rem; margin-bottom:0;'>📊 Gestão</h2>"
    "<p style='color:#6B7280; margin-top:0; margin-bottom:1rem;'>Visão interna — não compartilhar com corretores</p>",
    unsafe_allow_html=True,
)

# ── KPIs — Volume ─────────────────────────────────────────────────────────────
total_vendas   = len(df_vendas_fil)
total_locacoes = len(df_loc_fil)
total_negocios = total_vendas + total_locacoes

total_vgv = sum(float(r["vgv"] or 0) for r in resultados_todos)
ticket_medio = total_vgv / total_vendas if total_vendas > 0 else None

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("VGV do Período",      fmt_brl(total_vgv))
k2.metric("Ticket Médio",        fmt_brl(ticket_medio))
k3.metric("Negócios Fechados",   f"{total_negocios:,}")
k4.metric("Vendas",              f"{total_vendas:,}")
k5.metric("Locações",            f"{total_locacoes:,}")

# ── KPIs — Financeiro ─────────────────────────────────────────────────────────
total_agencia  = sum(float(r["comissao_agencia"] or 0) for r in resultados_todos)
total_gestao   = sum(float(r["r_gestao"] or 0) for r in resultados_todos)
total_corretor = sum(float(r["r_corretor"] or 0) for r in resultados_todos)
n_prime        = sum(1 for r in resultados_todos if r["nivel"] != "Base")
n_base         = sum(1 for r in resultados_todos if r["nivel"] == "Base")

if total_agencia > 0:
    liquido     = total_agencia - total_corretor - total_gestao
    pct_liquido = liquido / total_agencia * 100
else:
    liquido     = 0.0
    pct_liquido = None

k6, k7, k8, k9, k10 = st.columns(5)
k6.metric("Comissão Imobiliária",      fmt_brl(total_agencia))
k7.metric("Total Pago Corretores",     fmt_brl(total_corretor))
k8.metric("Total Pago à Gestão",       fmt_brl(total_gestao))
k9.metric(
    "% Líquido da Imobiliária",
    fmt_pct(pct_liquido),
    help="(Comissão − Corretores − Gestão) ÷ Comissão",
)
k10.metric("R$ Líquido Imobiliária",   fmt_brl(liquido if total_agencia > 0 else None))

k11, k12, *_ = st.columns(5)
k11.metric("Corretores Prime 🟢", n_prime)
k12.metric("Corretores Base ⚪",  n_base)

st.divider()

# ── Gráficos — Pizza Novo x Usado + Ranking VGV ───────────────────────────────
col_pizza, col_vgv_rank = st.columns(2)

with col_pizza:
    st.subheader("Tipo de Imóvel — Novo x Usado")

    tipo_counts = (
        df_vendas_fil["tipo_imovel"]
        .replace("", pd.NA)
        .dropna()
        .value_counts()
        .reset_index()
    )
    tipo_counts.columns = ["Tipo", "Qtd"]

    if not tipo_counts.empty:
        fig_pizza = go.Figure(go.Pie(
            labels=tipo_counts["Tipo"],
            values=tipo_counts["Qtd"],
            hole=0.45,
            textinfo="label+percent+value",
            marker_colors=[COR_AZUL, COR_PRIME2, COR_PRIME3],
        ))
        fig_pizza.update_layout(
            margin=dict(l=0, r=0, t=0, b=20),
            height=320,
            legend=dict(orientation="h", y=-0.1),
        )
        st.plotly_chart(fig_pizza, use_container_width=True)
    else:
        st.info("Sem dados de tipo de imóvel para este período.")

with col_vgv_rank:
    st.subheader("Ranking VGV por Corretor")
    st.caption("Ordem decrescente · locações excluídas")

    vgv_data = sorted(
        [(r["corretor"], float(r["vgv"] or 0), r["nivel"]) for r in resultados_todos],
        key=lambda x: x[1], reverse=True,
    )

    if vgv_data:
        nomes_v  = [d[0] for d in vgv_data]
        vals_v   = [d[1] for d in vgv_data]
        cores_v  = [COR_POR_NIVEL.get(d[2], COR_BASE) for d in vgv_data]
        labels_v = [fmt_brl(Decimal(str(v))) for v in vals_v]

        fig_vgv = go.Figure(go.Bar(
            x=vals_v, y=nomes_v,
            orientation="h",
            text=labels_v, textposition="outside",
            marker_color=cores_v,
        ))
        fig_vgv.add_vline(
            x=float(VGV_GATILHO_PRIME),
            line_dash="dash", line_color=COR_PRIME2,
            annotation_text="Meta Prime (R$ 2,1M)",
            annotation_position="top right",
            annotation_font_color=COR_PRIME2,
        )
        fig_vgv.update_layout(
            margin=dict(l=0, r=100, t=10, b=0),
            height=max(280, len(nomes_v) * 42),
            xaxis_title="VGV (R$)",
            yaxis=dict(autorange="reversed"),
        )
        st.plotly_chart(fig_vgv, use_container_width=True)
    else:
        st.info("Sem dados de VGV para este período.")

# ── Ranking nº Vendas + Ranking Captadores ────────────────────────────────────
col_vendas_rank, col_cap_rank = st.columns(2)

with col_vendas_rank:
    st.subheader("Ranking — Nº de Vendas por Corretor")

    vendas_sorted = sorted(resultados_todos, key=lambda x: x["num_vendas"], reverse=True)

    if vendas_sorted:
        nomes_nv = [r["corretor"] for r in vendas_sorted]
        qtds_nv  = [r["num_vendas"] for r in vendas_sorted]
        cores_nv = [COR_POR_NIVEL.get(r["nivel"], COR_BASE) for r in vendas_sorted]

        fig_nv = go.Figure(go.Bar(
            x=qtds_nv, y=nomes_nv,
            orientation="h",
            text=qtds_nv, textposition="outside",
            marker_color=cores_nv,
        ))
        fig_nv.update_layout(
            margin=dict(l=0, r=40, t=10, b=0),
            height=max(250, len(nomes_nv) * 42),
            xaxis_title="Número de Vendas",
            yaxis=dict(autorange="reversed"),
        )
        st.plotly_chart(fig_nv, use_container_width=True)

with col_cap_rank:
    st.subheader("Ranking de Captadores")
    st.caption("Corretores captadores e construtoras parceiras")

    df_cap = df_vendas_fil[
        df_vendas_fil["captador"].notna() &
        (df_vendas_fil["captador"] != "")
    ].copy()

    if not df_cap.empty:
        df_cap["valor_num"] = df_cap["valor"].apply(
            lambda v: float(v) if v is not None else 0.0
        )
        cap_rank = (
            df_cap.groupby("captador")
            .agg(vendas=("valor_num", "count"), vgv=("valor_num", "sum"))
            .reset_index()
            .sort_values("vgv", ascending=False)
        )
        cap_rank["vgv_fmt"] = cap_rank["vgv"].apply(
            lambda v: fmt_brl(Decimal(str(v))) if v else "—"
        )

        fig_cap = go.Figure(go.Bar(
            x=cap_rank["vgv"].tolist(),
            y=cap_rank["captador"].tolist(),
            orientation="h",
            text=cap_rank["vgv_fmt"].tolist(),
            textposition="outside",
            marker_color=COR_AZUL,
            customdata=cap_rank["vendas"].tolist(),
            hovertemplate="<b>%{y}</b><br>VGV: %{text}<br>Vendas: %{customdata}<extra></extra>",
        ))
        fig_cap.update_layout(
            margin=dict(l=0, r=100, t=10, b=0),
            height=max(250, len(cap_rank) * 42),
            xaxis_title="VGV (R$)",
            yaxis=dict(autorange="reversed"),
        )
        st.plotly_chart(fig_cap, use_container_width=True)
    else:
        st.info("Sem dados de captador para este período.")

# ══════════════════════════════════════════════════════════════════════════════
# SEÇÃO 2 — CORRETORES
# ══════════════════════════════════════════════════════════════════════════════
st.markdown(
    "<h2 style='margin-top:2rem; margin-bottom:0;'>👤 Corretores</h2>"
    "<p style='color:#6B7280; margin-top:0; margin-bottom:1rem;'>Desempenho individual por período</p>",
    unsafe_allow_html=True,
)

# Filtro de corretor específico (só afeta esta seção)
corretores_disp = sorted(df["corretor"].dropna().replace("", pd.NA).dropna().unique().tolist())
corretor_sel = st.multiselect("Filtrar por corretor", corretores_disp, placeholder="Todos os corretores")

if corretor_sel:
    df_corretores = df_fil[df_fil["corretor"].isin(corretor_sel)].copy()
else:
    df_corretores = df_fil.copy()

resultados_corretores = agregar_corretores(df_corretores, prime_herdado_set)

# KPIs resumidos da seção corretores
cor_total_vgv      = sum(float(r["vgv"] or 0) for r in resultados_corretores)
cor_total_vendas   = sum(r["num_vendas"] for r in resultados_corretores)
cor_total_locacoes = sum(r["num_locacoes"] for r in resultados_corretores)
cor_ticket         = cor_total_vgv / cor_total_vendas if cor_total_vendas > 0 else None
cor_total_com      = sum(float(r["r_corretor"] or 0) for r in resultados_corretores)

kc1, kc2, kc3, kc4 = st.columns(4)
kc1.metric("VGV",              fmt_brl(cor_total_vgv))
kc2.metric("Ticket Médio",     fmt_brl(cor_ticket))
kc3.metric("Negócios",         f"{cor_total_vendas + cor_total_locacoes:,}")
kc4.metric("Comissão Gerada",  fmt_brl(cor_total_com))

st.divider()

# Cards agrupados por nível Prime (pula níveis sem corretores)
for nivel in NIVEIS_ORDEM:
    grupo = [r for r in resultados_corretores if r["nivel"] == nivel]
    if not grupo:
        continue

    badge_label = BADGE_PRIME.get(nivel, nivel)
    st.markdown(f"**{badge_label}**")

    for r in grupo:
        corretor = r["corretor"]
        label    = badge_label
        if r["is_prime_herdado"] and nivel != "Base":
            label += " (H)"

        with st.container(border=True):
            col_nome, col_vendas, col_loc, col_vgv, col_com = st.columns([3, 1, 1, 2, 2])

            with col_nome:
                st.markdown(f"**{corretor}**")
                st.caption(label)

            col_vendas.metric("Vendas",   r["num_vendas"])
            col_loc.metric("Locações",    r["num_locacoes"])
            col_vgv.metric("VGV",         fmt_brl(r["vgv"]))
            col_com.metric("Comissão",    fmt_brl(r["r_corretor"]))

        if nivel == "Base":
            vgv_f     = float(r["vgv"] or 0)
            falta_vgv = max(float(VGV_GATILHO_PRIME) - vgv_f, 0)
            falta_v   = max(VENDAS_GATILHO_PRIME - r["num_vendas"], 0)
            msg = (
                f"Faltam {fmt_brl(falta_vgv)} em VGV  ou  {falta_v} venda(s) para Prime"
                if falta_vgv > 0 and falta_v > 0
                else "Atingiu o gatilho — aguardando confirmação Prime"
            )
            st.progress(r["progresso"], text=f"Progresso para Prime — {msg}")

    st.markdown("")  # espaço entre grupos de nível

st.caption("Dados atualizados a cada 5 min · Fonte: OP GANHAS + PRIME HERDADO")
