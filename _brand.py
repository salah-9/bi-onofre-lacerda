"""Identidade visual Onofre Lacerda — compartilhado entre todos os dashboards."""

from pathlib import Path
import streamlit as st

LOGO      = Path(__file__).parent / "logo_onofre.webp"
NAVY      = "#062b41"
GOLD      = "#cfaa52"
GOLD_DARK = "#b8943e"

_LIGHT = f"""
<style>
/* ── Sidebar ── */
section[data-testid="stSidebar"] {{
    background-color: {NAVY} !important;
    border-right: 3px solid {GOLD};
}}
section[data-testid="stSidebar"] * {{ color: #ffffff !important; }}
section[data-testid="stSidebar"] hr {{ border-color: {GOLD}55 !important; }}

/* ── Nav links ── */
[data-testid="stSidebarNavLink"] {{ color: #ffffff !important; border-radius: 6px; }}
[data-testid="stSidebarNavLink"]:hover,
[data-testid="stSidebarNavLink"][aria-selected="true"] {{
    background-color: {GOLD}33 !important;
    border-left: 3px solid {GOLD};
}}

/* ── Esconde só os botões Share/Star/Edit/GitHub ── */
[data-testid="stToolbar"] {{ display: none !important; }}

/* ── Headers ── */
h1, h2, h3 {{ color: {NAVY} !important; }}

/* ── Metrics ── */
[data-testid="stMetricValue"] {{
    color: {NAVY} !important;
    font-weight: 700;
    font-size: 1rem !important;
    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
}}
[data-testid="stMetricLabel"] {{ color: #555 !important; font-size: 0.7rem !important; }}

/* ── Divider ── */
hr {{ border-color: {GOLD}44 !important; }}

/* ── Buttons ── */
.stButton > button {{
    background-color: {GOLD};
    color: {NAVY};
    font-weight: 600;
    border: none;
}}
.stButton > button:hover {{ background-color: {GOLD_DARK}; }}

/* ── Mobile responsive ── */
@media (max-width: 768px) {{
    .main .block-container {{ padding: 0.75rem 0.75rem 2rem !important; max-width: 100% !important; }}
    div[data-testid="stHorizontalBlock"] {{ flex-wrap: wrap !important; gap: 0.5rem !important; }}
    div[data-testid="column"] {{ min-width: calc(50% - 0.5rem) !important; flex: 1 1 calc(50% - 0.5rem) !important; }}
    [data-testid="stMetricValue"] {{ font-size: 1.15rem !important; }}
    [data-testid="stMetricLabel"] {{ font-size: 0.65rem !important; }}
    h2, h3 {{ font-size: 1rem !important; }}
}}
@media (max-width: 480px) {{
    div[data-testid="column"] {{ min-width: 100% !important; flex: 1 1 100% !important; }}
}}
</style>
"""

_DARK = f"""
<style>
/* ── Main background ── */
.stApp, .main .block-container {{
    background-color: #0d1b2a !important;
    color: #e8e8e8 !important;
}}

/* ── Sidebar ── */
section[data-testid="stSidebar"] {{
    background-color: #061525 !important;
    border-right: 3px solid {GOLD};
}}
section[data-testid="stSidebar"] * {{ color: #ffffff !important; }}
section[data-testid="stSidebar"] hr {{ border-color: {GOLD}55 !important; }}

/* ── Nav links ── */
[data-testid="stSidebarNavLink"] {{ color: #ffffff !important; border-radius: 6px; }}
[data-testid="stSidebarNavLink"]:hover,
[data-testid="stSidebarNavLink"][aria-selected="true"] {{
    background-color: {GOLD}33 !important;
    border-left: 3px solid {GOLD};
}}

/* ── Esconde só os botões Share/Star/Edit/GitHub ── */
[data-testid="stToolbar"] {{ display: none !important; }}

/* ── Headers ── */
h1, h2, h3 {{ color: {GOLD} !important; }}

/* ── Text ── */
p, span, label, .stMarkdown {{ color: #dde3ec !important; }}

/* ── Metrics ── */
[data-testid="stMetricValue"] {{
    color: {GOLD} !important;
    font-weight: 700;
    font-size: 1rem !important;
    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
}}
[data-testid="stMetricLabel"] {{ color: #aab0ba !important; font-size: 0.7rem !important; }}

/* ── Cards ── */
[data-testid="stVerticalBlockBorderWrapper"] > div {{
    background-color: #162032 !important;
    border-color: #2a3a50 !important;
}}

/* ── Divider ── */
hr {{ border-color: {GOLD}44 !important; }}

/* ── Buttons ── */
.stButton > button {{ background-color: {GOLD}; color: {NAVY}; font-weight: 600; border: none; }}

/* ── Mobile responsive ── */
@media (max-width: 768px) {{
    .main .block-container {{ padding: 0.75rem 0.75rem 2rem !important; max-width: 100% !important; }}
    div[data-testid="stHorizontalBlock"] {{ flex-wrap: wrap !important; gap: 0.5rem !important; }}
    div[data-testid="column"] {{ min-width: calc(50% - 0.5rem) !important; flex: 1 1 calc(50% - 0.5rem) !important; }}
    [data-testid="stMetricValue"] {{ font-size: 1.15rem !important; }}
    [data-testid="stMetricLabel"] {{ font-size: 0.65rem !important; }}
    h2, h3 {{ font-size: 1rem !important; }}
}}
@media (max-width: 480px) {{
    div[data-testid="column"] {{ min-width: 100% !important; flex: 1 1 100% !important; }}
}}
</style>
"""


def setup() -> bool:
    if LOGO.exists():
        st.sidebar.image(str(LOGO), width=180)
    else:
        st.sidebar.markdown("### Onofre Lacerda")

    st.sidebar.divider()

    dark = st.sidebar.toggle("🌙 Tema Escuro", key="dark_mode",
                             value=st.session_state.get("dark_mode", False))

    st.sidebar.divider()

    st.markdown(_DARK if dark else _LIGHT, unsafe_allow_html=True)
    return dark
