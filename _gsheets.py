"""Autenticação Google Sheets — suporta OAuth local e Service Account na nuvem."""

from pathlib import Path
import streamlit as st

ROOT          = Path(__file__).parent
CLIENT_SECRET = ROOT / "client_secret.json"
TOKEN_DIR     = ROOT / ".auth"
SPREADSHEET_ID = "1yPE_XlMWbk1di6xK2bD68w5IbZkVi2JqILC0bXwEykc"


def get_client():
    """Retorna cliente gspread autenticado.
    - Em produção (Streamlit Cloud): usa Service Account via st.secrets
    - Local: usa OAuth via client_secret.json
    """
    import gspread

    if "gcp_service_account" in st.secrets:
        return gspread.service_account_from_dict(dict(st.secrets["gcp_service_account"]))

    return gspread.oauth(
        credentials_filename=str(CLIENT_SECRET),
        authorized_user_filename=str(TOKEN_DIR / "token.json"),
    )


def get_spreadsheet():
    return get_client().open_by_key(SPREADSHEET_ID)
