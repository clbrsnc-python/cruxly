import base64
import hashlib
import streamlit as st
from supabase import create_client, Client


def get_pkce_pair() -> tuple[str, str]:
    """Returns a deterministic (code_verifier, S256_code_challenge) pair for Streamlit OAuth."""
    seed = f"{st.secrets['SUPABASE_URL']}:{st.secrets['SUPABASE_ANON_KEY']}"
    code_verifier = hashlib.sha256(seed.encode("utf-8")).hexdigest()
    digest = hashlib.sha256(code_verifier.encode("ascii")).digest()
    code_challenge = base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")
    return code_verifier, code_challenge


def get_supabase() -> Client:
    """Returns the per-session authenticated Supabase client."""
    if "sb_client" not in st.session_state:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_ANON_KEY"]
        st.session_state["sb_client"] = create_client(url, key)
    return st.session_state["sb_client"]
