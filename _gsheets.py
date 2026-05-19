"""Autenticação Google Sheets — Service Account (nuvem) ou OAuth (local)."""

from pathlib import Path
import streamlit as st

ROOT          = Path(__file__).parent
CLIENT_SECRET = ROOT / "client_secret.json"
TOKEN_DIR     = ROOT / ".auth"
SPREADSHEET_ID = "1yPE_XlMWbk1di6xK2bD68w5IbZkVi2JqILC0bXwEykc"

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


@st.cache_resource
def get_client():
    import gspread

    # Service account via Streamlit secrets (produção — nunca expira)
    if "gcp_service_account" in st.secrets:
        from google.oauth2.service_account import Credentials
        creds = Credentials.from_service_account_info(
            dict(st.secrets["gcp_service_account"]),
            scopes=SCOPES,
        )
        return gspread.authorize(creds)

    # OAuth user token via Streamlit secrets (legado — pode expirar)
    if "oauth_token" in st.secrets:
        from google.oauth2.credentials import Credentials as OAuthCreds
        from google.auth.transport.requests import Request
        s = st.secrets["oauth_token"]
        # suporte a token dividido em duas partes para evitar quebra de linha no editor
        rt = s["refresh_token"]
        if "refresh_token_2" in s:
            rt = rt + s["refresh_token_2"]
        creds = OAuthCreds(
            token=None,
            refresh_token=rt,
            token_uri=s["token_uri"],
            client_id=s["client_id"],
            client_secret=s["client_secret"],
            scopes=SCOPES,
        )
        creds.refresh(Request())
        return gspread.authorize(creds)

    # OAuth local (desenvolvimento)
    return gspread.oauth(
        credentials_filename=str(CLIENT_SECRET),
        authorized_user_filename=str(TOKEN_DIR / "token.json"),
    )


@st.cache_resource
def get_spreadsheet():
    return get_client().open_by_key(SPREADSHEET_ID)
