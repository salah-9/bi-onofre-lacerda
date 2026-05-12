"""Autenticação por senha — Onofre Lacerda BI."""

from pathlib import Path
import streamlit as st

LOGO = Path(__file__).parent / "logo_onofre.webp"

NAVY = "#062b41"
GOLD = "#cfaa52"

_LOGIN_CSS = f"""
<style>
.stApp {{
    background-color: {NAVY} !important;
}}
.main .block-container {{
    background-color: {NAVY} !important;
    display: flex;
    justify-content: center;
    align-items: center;
    min-height: 80vh;
}}
div[data-testid="stVerticalBlockBorderWrapper"] {{
    background-color: #0d2a3e !important;
    border: 1px solid {GOLD}55 !important;
    border-radius: 12px !important;
}}
input[type="text"], input[type="password"] {{
    background-color: #0d2a3e !important;
    color: white !important;
    border: 1px solid {GOLD}88 !important;
    border-radius: 6px !important;
}}
label {{ color: #ccc !important; font-size: 0.85rem !important; }}
.stButton > button {{
    background-color: {GOLD} !important;
    color: {NAVY} !important;
    font-weight: 700 !important;
    width: 100% !important;
    border: none !important;
    padding: 0.6rem !important;
    border-radius: 6px !important;
    font-size: 1rem !important;
}}
header[data-testid="stHeader"] {{
    background-color: {NAVY} !important;
    height: 0 !important;
    min-height: 0 !important;
    border: none !important;
}}
[data-testid="stToolbar"] {{ display: none !important; }}
section[data-testid="stSidebar"] {{ display: none !important; }}
</style>
"""


def _get_users() -> dict:
    """Lê usuários dos Secrets ou usa fallback local."""
    if "users" in st.secrets:
        return dict(st.secrets["users"])
    return {}


def show_login() -> None:
    st.markdown(_LOGIN_CSS, unsafe_allow_html=True)

    col_a, col_b, col_c = st.columns([1, 2, 1])
    with col_b:
        with st.container(border=True):
            if LOGO.exists():
                st.image(str(LOGO), width=200)

            st.markdown(
                f"<h3 style='color:{GOLD}; text-align:center; margin-bottom:1.5rem;'>"
                "Área Restrita</h3>",
                unsafe_allow_html=True,
            )

            usuario = st.text_input("Usuário", placeholder="seu usuário")
            senha   = st.text_input("Senha", type="password", placeholder="••••••••")

            if st.button("Entrar"):
                users = _get_users()
                if usuario in users and users[usuario] == senha:
                    st.session_state["authenticated"] = True
                    st.session_state["usuario"] = usuario
                    st.rerun()
                else:
                    st.error("Usuário ou senha incorretos.")

            st.markdown(
                f"<p style='color:#888; font-size:0.7rem; text-align:center; margin-top:1.5rem;'>"
                "Onofre Lacerda Negócios Imobiliários</p>",
                unsafe_allow_html=True,
            )


def require_login() -> None:
    """Chame no início de cada página. Redireciona para login se não autenticado."""
    if not st.session_state.get("authenticated"):
        show_login()
        st.stop()
