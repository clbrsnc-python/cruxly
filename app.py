import streamlit as st
from supabase import create_client, Client

# ---------------------------------------------------------
# 1. PAGE CONFIG & GLOBAL VISUAL THEME (Times New Roman)
# ---------------------------------------------------------
st.set_page_config(
    page_title="Cruxly — Read deeper. Faster.",
    page_icon="cruxly_logo.jpg",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
    /* Global Times New Roman Typography */
    html, body, [class*="css"], .stApp, button, input, select, textarea, p, h1, h2, h3, h4, h5, h6, span, div {
        font-family: "Times New Roman", Times, serif !important;
    }

    /* Main Page Neutral Background */
    .stApp {
        background-color: #F4F6F9;
        color: #102033;
    }

    /* Deep Academic Blue Brand Banner */
    .cruxly-banner {
        background-color: #0B2545;
        border: 2px solid #D4AF37;
        border-radius: 12px;
        padding: 18px 24px;
        margin-bottom: 18px;
        color: #FFFFFF;
    }
    .cruxly-title {
        color: #E5C158;
        font-size: 2.6rem;
        font-weight: bold;
        margin: 0;
        line-height: 1.1;
        letter-spacing: 0.5px;
    }
    .cruxly-tagline {
        color: #F8E7B4;
        font-size: 1.15rem;
        font-style: italic;
        margin-top: 4px;
        margin-bottom: 0;
    }

    /* Static Vibrant Menu Bar (Zero Animation) */
    .static-nav {
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
        margin-bottom: 20px;
    }
    .nav-pill {
        padding: 8px 18px;
        border-radius: 6px;
        font-weight: bold;
        font-size: 1rem;
        color: #FFFFFF;
        text-decoration: none;
        border: 1px solid #0B2545;
        transition: none !important;
        animation: none !important;
    }
    .nav-home { background-color: #1B4965; }
    .nav-edition { background-color: #2A6F97; }
    .nav-archive { background-color: #7B2CBF; }
    .nav-saved { background-color: #2D6A4F; }
    .nav-prefs { background-color: #B5651D; }

    /* White News Card with Blue Border */
    .cruxly-card {
        background-color: #FFFFFF;
        border: 1.5px solid #1B4965;
        border-radius: 8px;
        padding: 18px 22px;
        margin-bottom: 16px;
        color: #102033;
    }

    /* High-Contrast Logout Button Styling */
    div.stButton > button {
        background-color: #0B2545 !important;
        color: #FFFFFF !important;
        border: 2px solid #D4AF37 !important;
        font-family: "Times New Roman", Times, serif !important;
        font-weight: bold !important;
        font-size: 1rem !important;
        border-radius: 6px !important;
        padding: 0.45rem 1.2rem !important;
        transition: none !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------
# 2. SUPABASE CLIENT INITIALIZATION
# ---------------------------------------------------------
@st.cache_resource
def get_supabase() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_ANON_KEY"]
    return create_client(url, key)


try:
    supabase = get_supabase()
except Exception:
    st.error("Platform configuration is incomplete. Please contact the Cruxly Administrator.")
    st.stop()

# ---------------------------------------------------------
# 3. OAUTH CALLBACK HANDLER (PKCE / CODE EXCHANGE)
# ---------------------------------------------------------
query_params = st.query_params
if "code" in query_params:
    try:
        auth_response = supabase.auth.exchange_code_for_session({"auth_code": query_params["code"]})
        if auth_response and auth_response.session:
            st.session_state["sb_session"] = auth_response.session
        st.query_params.clear()
        st.rerun()
    except Exception:
        st.query_params.clear()
        st.warning("Your sign-in session could not be verified. Please try signing in with Gmail again.")

# Restore active session if present
user = None
if "sb_session" in st.session_state:
    try:
        sess = st.session_state["sb_session"]
        supabase.auth.set_session(sess.access_token, sess.refresh_token)
        user_resp = supabase.auth.get_user()
        if user_resp and user_resp.user:
            user = user_resp.user
    except Exception:
        st.session_state.pop("sb_session", None)

# ---------------------------------------------------------
# 4. BRAND HEADER & LOGO RENDERING
# ---------------------------------------------------------
header_col1, header_col2 = st.columns([1.2, 4.8], vertical_alignment="center")
with header_col1:
    st.image("cruxly_logo.jpg", use_container_width=True)
with header_col2:
    st.markdown(
        """
        <div class="cruxly-banner">
            <div class="cruxly-title">Cruxly</div>
            <div class="cruxly-tagline">Read deeper. Faster.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ---------------------------------------------------------
# 5. AUTHENTICATION GATE & STATUS ROUTING
# ---------------------------------------------------------
if not user:
    st.markdown(
        """
        <div class="cruxly-card">
            <h3>Welcome to Cruxly — Bilingual News Intelligence</h3>
            <p>Sign in with your Gmail account to access verified, multi-source consolidated news reports in English and Bengali.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.button("Sign in with Gmail"):
        try:
            redirect_url = st.secrets.get("APP_REDIRECT_URL", "http://localhost:8501")
            res = supabase.auth.sign_in_with_oauth(
                {
                    "provider": "google",
                    "options": {"redirect_to": redirect_url},
                }
            )
            if res and res.url:
                st.markdown(f'<meta http-equiv="refresh" content="0;url={res.url}">', unsafe_allow_html=True)
                st.info("Redirecting to Google Sign-In...")
        except Exception:
            st.error("Unable to start Google Sign-In right now. Please try again shortly.")
else:
    # Top Bar with Logout
    top_l, top_r = st.columns([5, 1])
    with top_l:
        st.caption(f"Signed in as: **{user.email}**")
    with top_r:
        if st.button("Logout"):
            try:
                supabase.auth.sign_out()
            except Exception:
                pass
            st.session_state.pop("sb_session", None)
            st.rerun()

    # Fetch user profile & approval status
    try:
        profile_res = supabase.table("users").select("*").eq("id", user.id).single().execute()
        profile = profile_res.data
    except Exception:
        profile = None

    if not profile:
        st.warning("Your profile is being initialized. Please click Refresh below.")
        if st.button("Refresh Profile"):
            st.rerun()
    elif profile.get("account_status") == "pending":
        st.markdown(
            f"""
            <div class="cruxly-card">
                <h3>Account Awaiting Administrator Approval</h3>
                <p><strong>Name:</strong> {profile.get('full_name') or 'Registered User'}</p>
                <p><strong>Gmail:</strong> {profile.get('email')}</p>
                <p><strong>Status:</strong> Pending Review</p>
                <p>Your registration has been recorded. You will gain full access to Cruxly once an administrator approves your account.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    elif profile.get("account_status") == "rejected":
        st.error("Your access request was not approved by the administrator.")
    else:
        # Approved User View
        st.markdown(
            """
            <div class="static-nav">
                <span class="nav-pill nav-home">Live Feed</span>
                <span class="nav-pill nav-edition">Morning / Evening Editions</span>
                <span class="nav-pill nav-archive">3-Month Archive</span>
                <span class="nav-pill nav-saved">Saved News</span>
                <span class="nav-pill nav-prefs">Preferences</span>
            </div>
            <div class="cruxly-card">
                <h3>Cruxly Foundation Connected</h3>
                <p>Your account is approved and connected to Supabase. Next, we will wire up the automated RSS ingestion pipeline and live news feed.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
