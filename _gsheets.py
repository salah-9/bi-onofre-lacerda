"""Autenticação Google Sheets — suporta OAuth local e OAuth via Secrets na nuvem."""

from pathlib import Path
import streamlit as st

ROOT          = Path(__file__).parent
CLIENT_SECRET = ROOT / "client_secret.json"
TOKEN_DIR     = ROOT / ".auth"
SPREADSHEET_ID = "1yPE_XlMWbk1di6xK2bD68w5IbZkVi2JqILC0bXwEykc"


def get_client():
    import gspread
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request

    if "oauth_token" in st.secrets:
        s = st.secrets["oauth_token"]
        creds = Credentials(
            token=None,
            refresh_token=s["refresh_token"],
            token_uri=s["token_uri"],
            client_id=s["client_id"],
            client_secret=s["client_secret"],
            scopes=["https://www.googleapis.com/auth/spreadsheets",
                    "https://www.googleapis.com/auth/drive"],
        )
        creds.refresh(Request())
        return gspread.authorize(creds)

    return gspread.oauth(
        credentials_filename=str(CLIENT_SECRET),
        authorized_user_filename=str(TOKEN_DIR / "token.json"),
    )


def get_spreadsheet():
    return get_client().open_by_key(SPREADSHEET_ID)
