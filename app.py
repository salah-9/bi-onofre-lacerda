"""Página inicial — Sistema de BI Imobiliário."""

import streamlit as st

st.set_page_config(
    page_title="Onofre Lacerda — BI",
    page_icon="🏛️",
    layout="wide",
)

st.markdown("""
<style>
@media (max-width: 768px) {
    .main .block-container { padding: 0.75rem 0.75rem 2rem !important; max-width: 100% !important; }
    div[data-testid="stHorizontalBlock"] { flex-wrap: wrap !important; gap: 0.5rem !important; }
    div[data-testid="column"] { min-width: 100% !important; flex: 1 1 100% !important; }
}
</style>
""", unsafe_allow_html=True)

st.title("Onofre Lacerda — Business Intelligence")
st.caption("Selecione um dashboard no menu lateral")

st.divider()

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("### Comercial")
    st.markdown(
        "Funil de vendas, SLA de atendimento, ranking de corretores, "
        "ciclo de venda e motivos de perda."
    )
    st.page_link("pages/1_Comercial.py", label="Abrir Dashboard Comercial →")

with col2:
    st.markdown("### Financeiro")
    st.markdown(
        "Comissões por corretor, níveis Prime, VGV acumulado "
        "e progresso até a meta trimestral."
    )
    st.page_link("pages/2_Financeiro.py", label="Abrir Dashboard Financeiro →")

with col3:
    st.markdown("### Institucional")
    st.markdown(
        "Relatório white-label para construtoras: volume por campanha, "
        "qualificação de leads e evolução diária."
    )
    st.page_link("pages/3_Institucional.py", label="Abrir Relatório Institucional →")
