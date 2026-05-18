"""Autenticação por senha com persistência via cookie — Onofre Lacerda BI."""

import hmac
import hashlib
import streamlit as st
from streamlit_cookies_controller import CookieController

NAVY = "#062b41"
GOLD = "#cfaa52"
_COOKIE_NAME  = "ol_auth"
_COOKIE_MAX_AGE = 7 * 24 * 3600  # 7 dias

# CSS escuro aplicado antes de qualquer conteúdo
_DARK_CSS = f"""
<style>
.stApp {{ background-color: {NAVY} !important; }}
[data-testid="stToolbar"] {{ display: none !important; }}
header[data-testid="stHeader"] {{ background: transparent !important; border: none !important; }}
</style>
"""

_cookie_ctrl = CookieController()


def _secret() -> str:
    return st.secrets.get("cookie_secret", "ol-bi-secret-key-2025")


def _make_token(username: str) -> str:
    sig = hmac.new(_secret().encode(), username.encode(), hashlib.sha256).hexdigest()
    return f"{username}:{sig}"


def _verify_token(value: str) -> "str | None":
    try:
        username, sig = value.rsplit(":", 1)
        expected = hmac.new(_secret().encode(), username.encode(), hashlib.sha256).hexdigest()
        if hmac.compare_digest(expected, sig):
            return username
    except Exception:
        pass
    return None


def _get_users() -> dict:
    if "users" in st.secrets:
        return dict(st.secrets["users"])
    return {}


def _try_cookie_auth() -> bool:
    """Tenta restaurar sessão a partir do cookie. Retorna True se autenticado."""
    try:
        value = _cookie_ctrl.get(_COOKIE_NAME)
        if value:
            username = _verify_token(value)
            if username:
                st.session_state["authenticated"] = True
                st.session_state["usuario"] = username
                return True
    except Exception:
        pass
    return False


def show_login() -> None:
    st.markdown(_DARK_CSS, unsafe_allow_html=True)

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
                    _cookie_ctrl.set(_COOKIE_NAME, _make_token(usuario), max_age=_COOKIE_MAX_AGE)
                    st.rerun()
                else:
                    st.error("Usuário ou senha incorretos.")


def require_login() -> None:
    # Sessão já ativa neste run (caminho rápido — sem re-render)
    if st.session_state.get("authenticated"):
        return

    # Primeiro render: CookieController ainda não leu os cookies do browser.
    # Mostramos só o fundo escuro e paramos — o componente vai disparar um
    # segundo render automaticamente com os dados do cookie.
    if not st.session_state.get("_cookies_ready"):
        st.session_state["_cookies_ready"] = True
        st.markdown(_DARK_CSS, unsafe_allow_html=True)
        st.stop()

    # Segundo render em diante: cookies disponíveis — tenta restaurar sessão
    if _try_cookie_auth():
        return

    # Sem cookie válido → exibe login
    show_login()
    st.stop()
