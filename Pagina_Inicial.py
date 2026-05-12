"""Página inicial — BI Onofre Lacerda."""

import streamlit as st
import _brand
import _auth

st.set_page_config(
    page_title="BI Onofre Lacerda",
    page_icon="🏠",
    layout="wide",
)

_brand.setup()
_auth.require_login()

st.title("BI Onofre Lacerda")
st.caption("Selecione um dashboard no menu lateral")

st.divider()

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("### 📊 Comercial")
    st.markdown(
        "Funil de vendas, SLA de atendimento, ranking de corretores, "
        "ciclo de venda e motivos de perda."
    )
    st.page_link("pages/1_Comercial.py", label="Abrir Dashboard Comercial →")

with col2:
    st.markdown("### 💰 Financeiro")
    st.markdown(
        "Comissões por corretor, status Base / Prime, VGV acumulado "
        "e progresso até a meta trimestral."
    )
    st.page_link("pages/2_Financeiro.py", label="Abrir Dashboard Financeiro →")

with col3:
    st.markdown("### 🏢 Institucional")
    st.markdown(
        "Relatório para construtoras parceiras: volume por campanha, "
        "qualificação de leads e evolução diária."
    )
    st.page_link("pages/3_Institucional.py", label="Abrir Relatório Institucional →")
