import base64
import streamlit as st
from utils.supabase_client import get_pkce_pair, get_supabase
from views.public_pages import render_legal_page, render_public_landing
from views.reader_portal import render_reader_portal
from views.admin_portal import render_admin_portal

# ---------------------------------------------------------
# 1. PAGE CONFIG & GLOBAL VISUAL THEME (Times New Roman)
# ---------------------------------------------------------
st.set_page_config(
    page_title="Cruxly — Intelligent News for Intelligent Readers.",
    page_icon="cruxly_logo.jpg",
    layout="wide",
    initial_sidebar_state="collapsed",
)


def get_base64_image(image_path: str) -> str:
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode("utf-8")


logo_b64 = get_base64_image("cruxly_logo.jpg")

st.markdown(
    """
    <style>
    /* Global Times New Roman Typography (DPR v1.1 Section 8) */
    html, body, [class*="css"], .stApp, button, input, select, textarea, p, h1, h2, h3, h4, h5, h6, span, div, a {
        font-family: "Times New Roman", Times, serif !important;
    }

    /* Main Page Light Neutral Background */
    .stApp {
        background-color: #F4F6F9;
        color: #102033;
    }

    /* Flush Hero Header (Logo + Matching Height Deep Academic Blue Banner, Zero Gap) */
    .hero-wrapper {
        display: flex;
        align-items: stretch;
        width: 100%;
        height: 240px;
        margin-bottom: 14px;
        border-radius: 12px;
        overflow: hidden;
        border: 2px solid #D4AF37;
        background-color: #0B2545;
    }
    .hero-logo {
        height: 240px;
        width: 240px;
        object-fit: cover;
        display: block;
        flex-shrink: 0;
        border-right: 2px solid #D4AF37;
    }
    .hero-banner-content {
        flex: 1;
        background-color: #0B2545;
        padding: 24px 32px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        color: #FFFFFF;
    }
    .hero-welcome {
        color: #E5C158;
        font-size: 2.05rem;
        font-weight: bold;
        margin: 0 0 10px 0;
        line-height: 1.25;
    }
    .hero-subtext {
        color: #F8E7B4;
        font-size: 1.1rem;
        margin: 0;
    }

    /* High-Contrast Native Streamlit Buttons & Link Buttons */
    div.stButton > button,
    div[data-testid="stLinkButton"] > a {
        background-color: #0B2545 !important;
        color: #FFFFFF !important;
        border: 2px solid #D4AF37 !important;
        font-family: "Times New Roman", Times, serif !important;
        font-weight: bold !important;
        font-size: 1.05rem !important;
        border-radius: 6px !important;
        padding: 0.5rem 1.4rem !important;
        transition: none !important;
        animation: none !important;
        text-decoration: none !important;
    }
    div.stButton > button:hover,
    div[data-testid="stLinkButton"] > a:hover {
        background-color: #1B4965 !important;
        color: #E5C158 !important;
    }

    /* Static Vibrant Menu Bar (Zero Animation - DPR v1.1 Section 8) */
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
    .nav-admin { background-color: #8B1E3F; }

    /* White News & Information Cards with Blue Border */
    .cruxly-card {
        background-color: #FFFFFF;
        border: 1.5px solid #1B4965;
        border-radius: 8px;
        padding: 18px 22px;
        margin-bottom: 16px;
        color: #102033;
    }
    .cruxly-card h3 {
        color: #0B2545;
        margin-top: 0;
        margin-bottom: 8px;
        font-size: 1.3rem;
    }
    .cruxly-card p, .cruxly-card li {
        margin-top: 0;
        margin-bottom: 8px;
        font-size: 1.05rem;
        line-height: 1.5;
    }
    .badge-tag {
        display: inline-block;
        background-color: #E8EEF5;
        color: #0B2545;
        border: 1px solid #1B4965;
        padding: 2px 10px;
        border-radius: 4px;
        font-size: 0.85rem;
        font-weight: bold;
        margin-bottom: 8px;
    }

    /* Discreet Footer Note (DPR v1.1 Section 8 & 11) */
    .cruxly-footer {
        margin-top: 28px;
        padding: 16px 20px;
        background-color: #E8EEF5;
        border-top: 2px solid #1B4965;
        border-radius: 6px;
        font-size: 0.95rem;
        color: #102033;
        text-align: center;
        line-height: 1.6;
    }
    .cruxly-footer a {
        color: #0B2545;
        font-weight: bold;
        text-decoration: underline;
        margin: 0 8px;
    }

    @media (max-width: 768px) {
        .hero-wrapper {
            flex-direction: column;
            height: auto;
        }
        .hero-logo {
            width: 100%;
            height: auto;
            border-right: none;
            border-bottom: 2px solid #D4AF37;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------
# 2. INITIALIZE SUPABASE CLIENT
# ---------------------------------------------------------
try:
    supabase = get_supabase()
except Exception:
    st.error("Platform configuration is incomplete. Please contact the Cruxly Administrator.")
    st.stop()

# ---------------------------------------------------------
# 3. PUBLIC LEGAL & POLICY PAGES (?page=privacy / ?page=terms)
# ---------------------------------------------------------
query_params = st.query_params
active_page = query_params.get("page")

if active_page and render_legal_page(active_page, logo_b64):
    st.stop()

# ---------------------------------------------------------
# 4. OAUTH CALLBACK HANDLER (FROZEN RFC-7636 PKCE EXCHANGE)
# ---------------------------------------------------------
if "code" in query_params and "sb_session" not in st.session_state:
    try:
        code_verifier, _ = get_pkce_pair()
        auth_response = supabase.auth.exchange_code_for_session(
            {
                "auth_code": query_params["code"],
                "code_verifier": code_verifier,
            }
        )
        if auth_response and auth_response.session:
            st.session_state["sb_session"] = auth_response.session
            st.query_params.clear()
            st.rerun()
    except Exception as auth_exc:
        st.query_params.clear()
        st.error(f"Sign-in verification error: {auth_exc}")

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
# 5. ROUTE TO PUBLIC LANDING OR SIGNED-IN PORTALS
# ---------------------------------------------------------
if not user:
    render_public_landing(supabase, logo_b64)
else:
    st.markdown(
        f'<div class="hero-wrapper">'
        f'<img src="data:image/jpeg;base64,{logo_b64}" class="hero-logo" alt="Cruxly Logo" />'
        f'<div class="hero-banner-content">'
        f'<div class="hero-welcome">Welcome to Cruxly — Intelligent News for Intelligent Readers.</div>'
        f'<p class="hero-subtext">Signed in as: <strong>{user.email}</strong></p>'
        f'</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    _, logout_col = st.columns([5, 1])
    with logout_col:
        if st.button("Logout"):
            try:
                supabase.auth.sign_out()
            except Exception:
                pass
            st.session_state.pop("sb_session", None)
            st.session_state.pop("sb_client", None)
            st.rerun()

    profile = None
    profile_err = None
    try:
        profile_res = supabase.table("users").select("*").eq("id", user.id).maybe_single().execute()
        profile = profile_res.data
    except Exception as exc:
        profile_err = str(exc)

    if not profile:
        st.warning("Your profile is being initialized. Please click Refresh below.")
        if profile_err:
            st.caption(f"Diagnostic detail: {profile_err}")
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
        user_roles = profile.get("roles") or []
        is_admin = bool(set(user_roles) & {"super_admin", "user_admin"})

        render_reader_portal(supabase, user, profile)

        if is_admin:
            render_admin_portal(supabase, user.id, user_roles)

    st.markdown(
        """
        <div class="cruxly-footer">
            <strong>Cruxly — Read deeper. Faster.</strong> | Readers are encouraged to support journalism by purchasing original newspaper editions.<br/>
            <a href="?page=terms">Copyright, Attribution &amp; Terms</a> |
            <a href="?page=privacy">Privacy Policy</a>
        </div>
        """,
        unsafe_allow_html=True,
    )
