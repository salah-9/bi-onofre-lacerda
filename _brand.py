"""Identidade visual Onofre Lacerda — brandbook oficial."""

from pathlib import Path
import streamlit as st

LOGO = Path(__file__).parent / "logo_onofre.webp"

# Cores oficiais do brandbook
AZUL       = "#184D6C"   # tradição — primária
CREME      = "#FFFBD6"   # sobriedade — secundária
AZUL_DARK  = "#0d1e2d"   # background escuro
AZUL_CARD  = "#163d55"   # cards no tema escuro
AZUL_MID   = "#1a5f84"   # hover / gradiente


_BASE = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@400;600;700&family=Barlow+Condensed:wght@300;400;500;600&display=swap');

[data-testid="stToolbar"] { display: none !important; }

/* Sidebar — sempre azul da marca */
section[data-testid="stSidebar"] {
    background-color: #184D6C !important;
    border-right: 1px solid rgba(255,251,214,0.25) !important;
}
section[data-testid="stSidebar"] * { color: #FFFBD6 !important; }
section[data-testid="stSidebar"] hr { border-color: rgba(255,251,214,0.2) !important; }

[data-testid="stSidebarNavLink"] {
    color: #FFFBD6 !important;
    border-radius: 4px;
    font-family: 'Barlow Condensed', sans-serif !important;
    letter-spacing: 0.04em;
}
[data-testid="stSidebarNavLink"]:hover,
[data-testid="stSidebarNavLink"][aria-selected="true"] {
    background-color: rgba(255,251,214,0.15) !important;
    border-left: 3px solid #FFFBD6 !important;
}

/* Mobile */
@media (max-width: 768px) {
    .main .block-container {
        padding: 0.75rem 0.75rem 2rem !important;
        max-width: 100% !important;
    }
    div[data-testid="stHorizontalBlock"] { flex-wrap: wrap !important; gap: 0.5rem !important; }
    div[data-testid="column"] {
        min-width: calc(50% - 0.5rem) !important;
        flex: 1 1 calc(50% - 0.5rem) !important;
    }
    h2, h3 { font-size: 1rem !important; }
}
@media (max-width: 480px) {
    div[data-testid="column"] { min-width: 100% !important; flex: 1 1 100% !important; }
}
</style>
"""

_LIGHT = f"""
<style>
.stApp {{ background-color: #f8f9fb !important; }}

h1, h2, h3 {{
    color: {AZUL} !important;
    font-family: 'Cinzel', serif !important;
    letter-spacing: 0.04em;
}}
p, span, label, div {{ font-family: 'Barlow Condensed', sans-serif !important; }}

[data-testid="stMetricValue"] {{
    color: {AZUL} !important;
    font-family: 'Barlow Condensed', sans-serif !important;
    font-weight: 600;
    font-size: 1.15rem !important;
    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
}}
[data-testid="stMetricLabel"] {{
    color: #5a7080 !important;
    font-size: 0.68rem !important;
    font-family: 'Barlow Condensed', sans-serif !important;
    letter-spacing: 0.05em;
    text-transform: uppercase;
}}

[data-testid="stVerticalBlockBorderWrapper"] > div {{
    background-color: #ffffff !important;
    border: 1px solid {AZUL}22 !important;
    border-radius: 8px !important;
    box-shadow: 0 1px 4px rgba(24,77,108,0.08);
}}

hr {{ border-color: {AZUL}22 !important; }}

.stButton > button {{
    background-color: {AZUL} !important;
    color: {CREME} !important;
    font-family: 'Barlow Condensed', sans-serif !important;
    font-weight: 600;
    letter-spacing: 0.06em;
    border: none !important;
    border-radius: 4px;
}}
.stButton > button:hover {{ background-color: {AZUL_MID} !important; }}

[data-testid="stProgress"] > div > div {{ background-color: {AZUL} !important; }}

[data-testid="stSelectbox"] label,
[data-testid="stMultiSelect"] label {{
    color: {AZUL} !important;
    font-family: 'Barlow Condensed', sans-serif !important;
    font-weight: 600;
    letter-spacing: 0.04em;
}}
</style>
"""

_DARK = f"""
<style>
.stApp {{ background-color: {AZUL_DARK} !important; }}
.main .block-container {{ background-color: {AZUL_DARK} !important; color: {CREME} !important; }}

h1, h2, h3 {{
    color: {CREME} !important;
    font-family: 'Cinzel', serif !important;
    letter-spacing: 0.04em;
}}
p, span, label, div, .stMarkdown {{
    font-family: 'Barlow Condensed', sans-serif !important;
    color: #d4e4ef !important;
}}

[data-testid="stMetricValue"] {{
    color: {CREME} !important;
    font-family: 'Barlow Condensed', sans-serif !important;
    font-weight: 600;
    font-size: 1.15rem !important;
    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
}}
[data-testid="stMetricLabel"] {{
    color: #7aaabb !important;
    font-size: 0.68rem !important;
    font-family: 'Barlow Condensed', sans-serif !important;
    letter-spacing: 0.05em;
    text-transform: uppercase;
}}

[data-testid="stVerticalBlockBorderWrapper"] > div {{
    background-color: {AZUL_CARD} !important;
    border: 1px solid rgba(255,251,214,0.15) !important;
    border-radius: 8px !important;
}}

hr {{ border-color: rgba(255,251,214,0.15) !important; }}

.stButton > button {{
    background-color: {CREME} !important;
    color: {AZUL} !important;
    font-family: 'Barlow Condensed', sans-serif !important;
    font-weight: 700;
    letter-spacing: 0.06em;
    border: none !important;
    border-radius: 4px;
}}
.stButton > button:hover {{ opacity: 0.9; }}

[data-testid="stProgress"] > div > div {{
    background-color: {CREME} !important;
    opacity: 0.75;
}}

/* Inputs */
[data-testid="stSelectbox"] > div > div,
[data-testid="stMultiSelect"] > div > div {{
    background-color: {AZUL_CARD} !important;
    border-color: rgba(255,251,214,0.25) !important;
    color: {CREME} !important;
}}
[data-testid="stSelectbox"] label,
[data-testid="stMultiSelect"] label {{
    color: {CREME} !important;
    font-family: 'Barlow Condensed', sans-serif !important;
    font-weight: 500;
    letter-spacing: 0.04em;
}}

/* Tabs */
[data-testid="stTabs"] [role="tab"] {{
    font-family: 'Barlow Condensed', sans-serif !important;
    letter-spacing: 0.06em;
    color: #9ab5c8 !important;
}}
[data-testid="stTabs"] [role="tab"][aria-selected="true"] {{
    color: {CREME} !important;
    border-bottom-color: {CREME} !important;
}}
</style>
"""


def setup() -> bool:
    if LOGO.exists():
        st.sidebar.image(str(LOGO), width=180)
    else:
        st.sidebar.markdown(
            f"<h3 style='color:{CREME}; font-family:Cinzel,serif; letter-spacing:0.05em;'>Onofre Lacerda</h3>",
            unsafe_allow_html=True,
        )

    st.sidebar.divider()

    dark = st.sidebar.toggle(
        "🌙 Tema Escuro",
        key="dark_mode",
        value=st.session_state.get("dark_mode", True),
    )

    st.sidebar.divider()

    st.markdown(_BASE, unsafe_allow_html=True)
    st.markdown(_DARK if dark else _LIGHT, unsafe_allow_html=True)
    return dark
