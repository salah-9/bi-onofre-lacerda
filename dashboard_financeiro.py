"""Dashboard Financeiro — Comissões da equipe comercial."""

import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from decimal import Decimal

sys.path.insert(0, str(Path(__file__).parent))
from commission.calculator import (
    Venda, calcular_comissao, relatorio_trimestre, trimestre_de_data,
    VGV_GATILHO_PRIME, VENDAS_GATILHO_PRIME, TAXA_MAXIMA, TAXA_INTERMEDIACAO,
)

ROOT = Path(__file__).parent
CLIENT_SECRET = ROOT / "client_secret.json"
TOKEN_DIR     = ROOT / ".auth"
SPREADSHEET_ID = "1yPE_XlMWbk1di6xK2bD68w5IbZkVi2JqILC0bXwEykc"

st.set_page_config(
    page_title="Dashboard Financeiro",
    page_icon="💰",
    layout="wide",
)

COR_PRIME  = "#22C55E"
COR_BASE   = "#6B7280"
COR_FUNDO_PRIME = "#F0FDF4"
COR_AZUL   = "#1E6FE8"

# ── Helpers ──────────────────────────────────────────────────────────────────
FORMATOS_COM_ANO  = ["%d/%m/%Y %H:%M:%S", "%d/%m/%Y %H:%M", "%d/%m/%Y",
                     "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"]
FORMATOS_SEM_ANO  = ["%d/%m %H:%M:%S", "%d/%m %H:%M", "%d/%m"]
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
    for fmt in FORMATOS_COM_ANO:
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


def fmt_brl(v: float) -> str:
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def fmt_pct(v: float) -> str:
    return f"{v * 100:.0f}%"


# ── Carga de dados ────────────────────────────────────────────────────────────
@st.cache_data(ttl=300, show_spinner="Carregando dados da planilha...")
def carregar_vendas() -> list[Venda]:
    import gspread
    gc = gspread.oauth(
        credentials_filename=str(CLIENT_SECRET),
        authorized_user_filename=str(TOKEN_DIR / "token.json"),
    )
    sh  = gc.open_by_key(SPREADSHEET_ID)
    ws  = sh.worksheet("OP GANHAS")
    rows = ws.get_all_records()

    vendas = []
    for row in rows:
        won_raw    = str(row.get("Data Ganhou", "")).strip()
        valor_raw  = str(row.get("Valor ", row.get("Valor", ""))).strip()
        corretor   = str(row.get("Responsavel", "")).strip()
        tipo_raw   = str(row.get("Tipo de Negocio", "")).strip().lower()

        if not won_raw or not valor_raw or not corretor:
            continue
        if "loca" in tipo_raw:
            continue

        dt = parse_dt(won_raw)
        if not dt:
            continue

        valor_clean = (
            valor_raw.replace("R$", "").replace(".", "").replace(",", ".").strip()
        )
        try:
            valor = Decimal(valor_clean)
        except Exception:
            continue

        vendas.append(Venda(
            lead_id=str(row.get("ID lead", "")),
            corretor=corretor,
            trimestre=trimestre_de_data(dt.strftime("%Y-%m-%dT%H:%M:%S")),
            valor=valor,
            contract_type="venda",
        ))

    return vendas


# ── Layout ────────────────────────────────────────────────────────────────────
st.title("Dashboard Financeiro")
st.caption("Comissões · Status Base / Prime · Valor a pagar")

vendas = carregar_vendas()

trimestres = sorted({v.trimestre for v in vendas}, reverse=True)
if not trimestres:
    st.error("Nenhuma venda encontrada na planilha.")
    st.stop()

col_f, _ = st.columns([2, 5])
with col_f:
    trimestre_sel = st.selectbox("Trimestre", trimestres)

resultados = relatorio_trimestre(trimestre_sel, vendas)

# ── KPIs ──────────────────────────────────────────────────────────────────────
st.divider()

total_vgv          = sum(float(r.vgv)          for r in resultados)
total_base_calculo = sum(float(r.base_calculo) for r in resultados)
total_comissao     = sum(float(r.comissao)     for r in resultados)
n_prime            = sum(1 for r in resultados if r.status == "Prime")
n_base             = sum(1 for r in resultados if r.status == "Base")

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("VGV do Trimestre",         fmt_brl(total_vgv))
k2.metric("Comissão Imobiliária (6%)", fmt_brl(total_base_calculo))
k3.metric("Total a Pagar Corretores", fmt_brl(total_comissao))
k4.metric("Corretores Prime 🟢",      n_prime)
k5.metric("Corretores Base ⚪",       n_base)

st.divider()

# ── Tabela de comissões ───────────────────────────────────────────────────────
st.subheader("Comissões por Corretor")

for r in resultados:
    is_prime = r.status == "Prime"
    cor_borda = COR_PRIME if is_prime else "#E5E7EB"
    badge_cor = COR_PRIME if is_prime else COR_BASE

    with st.container():
        st.markdown(
            f"""
            <div style="
                border-left: 5px solid {cor_borda};
                background: {'#F0FDF4' if is_prime else '#FAFAFA'};
                border-radius: 8px;
                padding: 14px 20px;
                margin-bottom: 10px;
            ">
                <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px;">
                    <div style="flex:2; min-width:140px;">
                        <div style="font-size:17px; font-weight:600; color:#111;">{r.corretor}</div>
                        <div style="margin-top:4px;">
                            <span style="
                                background:{badge_cor}22;
                                color:{badge_cor};
                                border:1px solid {badge_cor};
                                border-radius:4px;
                                padding:2px 10px;
                                font-size:12px;
                                font-weight:600;
                            ">{r.status}</span>
                        </div>
                    </div>
                    <div style="flex:1; min-width:80px; text-align:center;">
                        <div style="font-size:11px; color:#6B7280; text-transform:uppercase;">Vendas</div>
                        <div style="font-size:20px; font-weight:700;">{r.num_vendas}</div>
                    </div>
                    <div style="flex:2; min-width:130px; text-align:center;">
                        <div style="font-size:11px; color:#6B7280; text-transform:uppercase;">VGV (imóveis)</div>
                        <div style="font-size:16px; font-weight:600;">{fmt_brl(float(r.vgv))}</div>
                    </div>
                    <div style="flex:2; min-width:130px; text-align:center;">
                        <div style="font-size:11px; color:#6B7280; text-transform:uppercase;">Comissão Imob. (6%)</div>
                        <div style="font-size:16px; font-weight:600;">{fmt_brl(float(r.base_calculo))}</div>
                    </div>
                    <div style="flex:1; min-width:60px; text-align:center;">
                        <div style="font-size:11px; color:#6B7280; text-transform:uppercase;">Taxa</div>
                        <div style="font-size:20px; font-weight:700; color:{badge_cor};">{fmt_pct(float(r.taxa))}</div>
                    </div>
                    <div style="flex:2; min-width:160px; text-align:right;">
                        <div style="font-size:11px; color:#6B7280; text-transform:uppercase;">A Pagar ao Corretor</div>
                        <div style="font-size:20px; font-weight:700; color:#111;">{fmt_brl(float(r.comissao))}</div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Barra de progresso para corretores Base
        if not is_prime:
            vgv_f     = float(r.vgv)
            vgv_meta  = float(VGV_GATILHO_PRIME)
            vend_meta = int(VENDAS_GATILHO_PRIME)

            prog_vgv  = min(vgv_f / vgv_meta, 1.0)
            prog_vend = min(r.num_vendas / vend_meta, 1.0)
            prog      = max(prog_vgv, prog_vend)

            falta_vgv  = max(vgv_meta - vgv_f, 0)
            falta_vend = max(vend_meta - r.num_vendas, 0)

            if falta_vgv > 0 and falta_vend > 0:
                msg = f"Faltam {fmt_brl(falta_vgv)} em VGV  ou  {falta_vend} venda(s) para Prime"
            else:
                msg = "Atingiu o gatilho — será Prime no próximo cálculo"

            st.progress(prog, text=f"Progresso para Prime — {msg}")

st.divider()

# ── Gráfico VGV por corretor ──────────────────────────────────────────────────
st.subheader("VGV por Corretor (valor dos imóveis)")

nomes   = [r.corretor  for r in resultados]
vgvs    = [float(r.vgv) for r in resultados]
cores   = [COR_PRIME if r.status == "Prime" else COR_BASE for r in resultados]
labels  = [fmt_brl(v) for v in vgvs]

fig = go.Figure(go.Bar(
    x=vgvs,
    y=nomes,
    orientation="h",
    text=labels,
    textposition="outside",
    marker_color=cores,
))

fig.add_vline(
    x=float(VGV_GATILHO_PRIME),
    line_dash="dash",
    line_color=COR_PRIME,
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

st.caption(f"Dados atualizados a cada 5 min · Locações excluídas · Taxa de intermediação: 6% · Planilha: Cópia de OL LEADS GERAIS dash 2")
