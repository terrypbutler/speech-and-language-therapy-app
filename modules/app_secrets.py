"""Safe access to optional Streamlit secrets."""

import streamlit as st
from streamlit.errors import StreamlitSecretNotFoundError


def get_secret(name: str) -> str | None:
    """Return a configured secret without failing when no secrets file exists."""

    try:
        value = st.secrets.get(name)
    except StreamlitSecretNotFoundError:
        return None
    if value is None:
        return None
    clean = str(value).strip()
    return clean or None
