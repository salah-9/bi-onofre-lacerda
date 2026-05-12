"""Autenticação por senha — Onofre Lacerda BI."""

import streamlit as st

NAVY = "#062b41"
GOLD = "#cfaa52"

_LOGIN_CSS = f"""
<style>
.stApp {{ background-color: {NAVY} !important; }}
[data-testid="stToolbar"] {{ display: none !important; }}
header[data-testid="stHeader"] {{ background: transparent !important; border: none !important; }}
</style>
"""


def is_authenticated() -> bool:
    return st.session_state.get("authenticated", False)


def _get_users() -> dict:
    if "users" in st.secrets:
        return dict(st.secrets["users"])
    return {}


def show_login() -> None:
    st.markdown(_LOGIN_CSS, unsafe_allow_html=True)

    col_a, col_b, col_c = st.columns([1, 2, 1])
    with col_b:
        with st.container(border=True):
            st.markdown(
                f"<h2 style='color:{GOLD}; text-align:center;'>Onofre Lacerda</h2>"
                f"<p style='color:#aaa; text-align:center; margin-bottom:1.5rem;'>Área Restrita</p>",
                unsafe_allow_html=True,
            )

            usuario = st.text_input("Usuário", placeholder="seu usuário")
            senha   = st.text_input("Senha", type="password", placeholder="••••••••")

            if st.button("Entrar", use_container_width=True):
                users = _get_users()
                if usuario in users and users[usuario] == senha:
                    st.session_state["authenticated"] = True
                    st.session_state["usuario"] = usuario
                    st.rerun()
                else:
                    st.error("Usuário ou senha incorretos.")


def require_login() -> None:
    """Chame ANTES de _brand.setup(). Para execução se não autenticado."""
    if not is_authenticated():
        show_login()
        st.stop()
