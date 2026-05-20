"""Identidade visual Onofre Lacerda — brandbook oficial."""

import base64
from pathlib import Path
import streamlit as st

_ASSETS    = Path(__file__).parent / "assets"
LOGO       = _ASSETS / "logo_onofre.png"
LOGO_LIGHT = _ASSETS / "logo_onofre_light.png"
_FONT_DIR  = Path(__file__).parent / "fonts"

AZUL      = "#184D6C"
CREME     = "#FFFBD6"
AZUL_DARK = "#0d1e2d"
AZUL_CARD = "#163d55"
AZUL_MID  = "#1a5f84"


def _b64(path: Path) -> str:
    try:
        return base64.b64encode(path.read_bytes()).decode()
    except Exception:
        return ""


def _font_face(name: str, b64: str, fmt: str, weight: int = 400) -> str:
    if not b64:
        return ""
    return (
        f"@font-face{{"
        f"font-family:'{name}';"
        f"src:url('data:font/{fmt};base64,{b64}') format('{fmt}');"
        f"font-weight:{weight};font-display:swap;}}\n"
    )


def _fonts_css() -> str:
    css = "<style>\n"
    css += _font_face("TrajanPro", _b64(_FONT_DIR / "trajan" / "TrajanPro-Regular.ttf"), "truetype", 400)
    css += _font_face("TrajanPro", _b64(_FONT_DIR / "trajan" / "TrajanPro-Bold.otf"),    "opentype", 700)
    css += _font_face("SwitzCond", _b64(_FONT_DIR / "switzerland" / "Switzerland_Condensed_Plain.ttf"), "truetype", 400)
    css += _font_face("SwitzCond", _b64(_FONT_DIR / "switzerland" / "Switzerland_Condensed_Bold.ttf"),  "truetype", 700)
    css += "</style>"
    return css


_STYLE = f"""
<style>
/* ── Toolbar ── */
[data-testid="stToolbar"] {{display:none !important;}}

/* ── Sidebar ── */
[data-testid="stSidebar"] {{
    background-color: {AZUL} !important;
    border-right: 1px solid rgba(255,251,214,0.2) !important;
}}
[data-testid="stSidebar"] * {{color: {CREME} !important;}}
[data-testid="stSidebar"] hr {{border-color: rgba(255,251,214,0.2) !important;}}

/* Nav links */
[data-testid="stSidebarNavLink"] {{
    color: {CREME} !important;
    border-radius: 3px;
    font-family: 'SwitzCond', sans-serif !important;
    letter-spacing: 0.05em;
    font-size: 0.9rem !important;
}}
[data-testid="stSidebarNavLink"]:hover,
[data-testid="stSidebarNavLink"][aria-selected="true"] {{
    background: rgba(255,251,214,0.12) !important;
    border-left: 3px solid {CREME} !important;
}}

/* ── Fundo principal ── */
.stApp, .main .block-container {{
    background-color: {AZUL_DARK} !important;
}}

/* ── Tipografia ── */
h1 {{
    font-family: 'TrajanPro', serif !important;
    color: {CREME} !important;
    letter-spacing: 0.06em !important;
    font-size: 1.5rem !important;
    border-bottom: 1px solid rgba(255,251,214,0.2);
    padding-bottom: 0.5rem;
    margin-bottom: 0.25rem !important;
}}
h2, h3 {{
    font-family: 'TrajanPro', serif !important;
    color: {CREME} !important;
    letter-spacing: 0.05em !important;
}}
p, span, label, div, small {{
    font-family: 'SwitzCond', sans-serif !important;
}}
.stCaption, [data-testid="stCaptionContainer"] * {{
    color: rgba(255,251,214,0.55) !important;
    font-family: 'SwitzCond', sans-serif !important;
    letter-spacing: 0.03em;
}}

/* ── Métricas ── */
[data-testid="stMetricValue"] {{
    color: {CREME} !important;
    font-family: 'SwitzCond', sans-serif !important;
    font-weight: 700 !important;
    font-size: 1.25rem !important;
    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
}}
[data-testid="stMetricLabel"] {{
    color: rgba(255,251,214,0.6) !important;
    font-family: 'SwitzCond', sans-serif !important;
    font-size: 0.65rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.07em !important;
}}
[data-testid="stMetricDelta"] {{color: #4ade80 !important;}}

/* ── Cards / containers ── */
[data-testid="stVerticalBlockBorderWrapper"] > div {{
    background-color: {AZUL_CARD} !important;
    border: 1px solid rgba(255,251,214,0.12) !important;
    border-radius: 6px !important;
}}

/* ── Divider ── */
hr {{border-color: rgba(255,251,214,0.15) !important;}}

/* ── Tabs ── */
[data-testid="stTabs"] [role="tablist"] {{
    border-bottom: 1px solid rgba(255,251,214,0.15) !important;
}}
[data-testid="stTabs"] [role="tab"] {{
    color: rgba(255,251,214,0.5) !important;
    font-family: 'SwitzCond', sans-serif !important;
    letter-spacing: 0.07em !important;
    font-size: 0.85rem !important;
    text-transform: uppercase !important;
}}
[data-testid="stTabs"] [role="tab"][aria-selected="true"] {{
    color: {CREME} !important;
    border-bottom: 2px solid {CREME} !important;
}}

/* ── Selectbox / Multiselect ── */
[data-testid="stSelectbox"] label,
[data-testid="stMultiSelect"] label {{
    color: rgba(255,251,214,0.7) !important;
    font-family: 'SwitzCond', sans-serif !important;
    font-size: 0.72rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.06em !important;
}}
[data-testid="stSelectbox"] > div > div,
[data-testid="stMultiSelect"] > div > div {{
    background-color: {AZUL_CARD} !important;
    border: 1px solid rgba(255,251,214,0.2) !important;
    color: {CREME} !important;
}}

/* ── Botões ── */
.stButton > button {{
    background-color: {CREME} !important;
    color: {AZUL} !important;
    border: none !important;
    font-family: 'SwitzCond', sans-serif !important;
    font-weight: 700 !important;
    letter-spacing: 0.06em !important;
    border-radius: 3px !important;
}}
.stButton > button:hover {{opacity: 0.88 !important;}}

/* ── Progress bars ── */
[data-testid="stProgress"] > div > div {{
    background-color: {CREME} !important;
    opacity: 0.6 !important;
}}

/* ── Toggle ── */
[data-testid="stToggle"] label {{
    color: {CREME} !important;
    font-family: 'SwitzCond', sans-serif !important;
}}

/* ── Seções internas (Gestão / Corretores) ── */
.ol-section {{
    border-left: 3px solid {CREME};
    padding: 0.5rem 1rem;
    margin: 2rem 0 1rem 0;
    background: rgba(255,251,214,0.04);
    border-radius: 0 4px 4px 0;
}}
.ol-section-title {{
    font-family: 'TrajanPro', serif !important;
    letter-spacing: 0.1em;
    font-size: 0.78rem;
    text-transform: uppercase;
    font-weight: 700;
    margin: 0;
    color: {CREME} !important;
}}
.ol-section-sub {{
    font-family: 'SwitzCond', sans-serif !important;
    font-size: 0.7rem;
    margin: 0.1rem 0 0 0;
    color: rgba(255,251,214,0.5) !important;
}}

/* ── Mobile ── */
@media (max-width: 768px) {{
    .main .block-container {{padding: 0.75rem !important; max-width: 100% !important;}}
    div[data-testid="stHorizontalBlock"] {{flex-wrap: wrap !important;}}
    div[data-testid="column"] {{min-width: calc(50% - 0.5rem) !important; flex: 1 1 calc(50% - 0.5rem) !important;}}
}}
@media (max-width: 480px) {{
    div[data-testid="column"] {{min-width: 100% !important; flex: 1 1 100% !important;}}
}}
</style>
"""


def setup() -> None:
    # Logo centralizado na sidebar
    logo_path = LOGO_LIGHT if LOGO_LIGHT.exists() else (LOGO if LOGO.exists() else None)
    if logo_path:
        b64 = _b64(logo_path)
        st.sidebar.markdown(
            f'<div style="text-align:center;padding:1.2rem 0.5rem 0.2rem;">'
            f'<img src="data:image/png;base64,{b64}" '
            f'style="width:100%;max-width:220px;display:block;margin:0 auto;">'
            f'</div>',
            unsafe_allow_html=True,
        )
    else:
        st.sidebar.markdown(
            f'<div style="text-align:center;padding:1rem 0;">'
            f'<span style="color:{CREME};font-family:TrajanPro,serif;'
            f'letter-spacing:.06em;font-size:.85rem;">ONOFRE LACERDA</span></div>',
            unsafe_allow_html=True,
        )

    st.sidebar.divider()
    st.sidebar.markdown(
        f'<span style="color:rgba(255,251,214,0.6);font-family:SwitzCond,sans-serif;'
        f'font-size:.7rem;letter-spacing:.05em;">NAVEGAÇÃO</span>',
        unsafe_allow_html=True,
    )
    st.sidebar.divider()

    # Injeta fontes e CSS
    st.markdown(_fonts_css(), unsafe_allow_html=True)
    st.markdown(_STYLE, unsafe_allow_html=True)
