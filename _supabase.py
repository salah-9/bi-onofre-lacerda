"""Supabase client — substitui _gsheets.py."""

import streamlit as st


@st.cache_resource
def get_client():
    from supabase import create_client
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)


def get_all_records(table: str) -> list[dict]:
    """Retorna todos os registros de uma tabela, paginando automaticamente."""
    client = get_client()
    all_data: list[dict] = []
    page_size = 1000
    offset = 0
    while True:
        resp = (
            client.table(table)
            .select("*")
            .range(offset, offset + page_size - 1)
            .execute()
        )
        all_data.extend(resp.data)
        if len(resp.data) < page_size:
            break
        offset += page_size
    return all_data
