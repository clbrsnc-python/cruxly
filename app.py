import base64
from datetime import datetime
import pytz
import streamlit as st
from utils.supabase_client import get_pkce_pair, get_supabase
from views.public_pages import render_legal_page, render_public_landing
from views.reader_portal import render_reader_portal
from views.admin_portal import render_admin_portal

IST = pytz.timezone("Asia/Kolkata")

# ---------------------------------------------------------
# 1. PAGE CONFIG & GLOBAL EDITORIAL BROADSHEET THEME
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
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&family=Noto+Serif+Bengali:wght@400;600;700&family=Playfair+Display:ital,wght@0,600;0,700;0,800;1,600&display=swap');

    /* Global Editorial Typography */
    html, body, [class*="css"], .stApp, button, input, select, textarea, p, h1, h2, h3, h4, h5, h6, span, div, a {
        font-family: "Times New Roman", "Playfair Display", Georgia, serif !important;
    }

    /* Main Page Aged-Newsprint Neutral Background */
    .stApp {
        background-color: #F4F1EA;
        color: #1D120A;
    }

    /* Equal-Height Split-Screen Columns */
    div[data-testid="stHorizontalBlock"] {
        align-items: stretch !important;
    }
    div[data-testid="stColumn"] > div {
        height: 100%;
    }

    /* ---------------------------------------------------------
       SPLIT-SCREEN PUBLIC LANDING PAGE (BURGUNDY + PRINT BROADSHEET)
       --------------------------------------------------------- */
    .landing-brand-panel {
        background: linear-gradient(165deg, #3C0612 0%, #26030B 100%);
        border: 2px solid #D4AF37;
        border-radius: 14px;
        padding: 24px 22px 18px 22px;
        color: #FBF9F4;
        text-align: center;
        box-shadow: 0 8px 24px rgba(29, 18, 10, 0.16);
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    .landing-logo-img {
        width: 210px;
        height: 210px;
        object-fit: cover;
        border-radius: 16px;
        border: 2.5px solid #D4AF37;
        margin: 0 auto 16px auto;
        display: block;
        box-shadow: 0 6px 18px rgba(0, 0, 0, 0.4);
    }
    .landing-feature-pill {
        background-color: rgba(255, 255, 255, 0.07);
        border: 1px solid rgba(212, 175, 55, 0.65);
        border-radius: 8px;
        padding: 8px 14px;
        margin: 0 auto 8px auto;
        width: 100%;
        max-width: 410px;
        font-size: 0.94rem;
        font-weight: 600;
        color: #FBF9F4;
        text-align: left;
        box-sizing: border-box;
    }

    /* Native st.link_button styled with Multicolor Google "G" Icon (Top-Frame Safe) */
    .google-btn-holder {
        display: flex;
        justify-content: center;
        margin: 14px auto 10px auto;
    }
    .google-btn-holder + div[data-testid="stLinkButton"],
    div[data-testid="stColumn"]:first-child div[data-testid="stLinkButton"] {
        display: flex !important;
        justify-content: center !important;
        margin: 12px auto 10px auto !important;
    }
    div[data-testid="stColumn"]:first-child div[data-testid="stLinkButton"] > a {
        background-color: #FFFFFF !important;
        color: #1F1F1F !important;
        border: 2px solid #D4AF37 !important;
        border-radius: 8px !important;
        padding: 10px 24px !important;
        font-family: "Inter", "Times New Roman", sans-serif !important;
        font-size: 1.03rem !important;
        font-weight: 700 !important;
        display: inline-flex !important;
        align-items: center !important;
        gap: 10px !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.28) !important;
    }
    div[data-testid="stColumn"]:first-child div[data-testid="stLinkButton"] > a::before {
        content: "";
        display: inline-block;
        width: 20px;
        height: 20px;
        flex-shrink: 0;
        background-repeat: no-repeat;
        background-size: contain;
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 48 48'%3E%3Cpath fill='%23EA4335' d='M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5z'/%3E%3Cpath fill='%234285F4' d='M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.94c-.58 2.96-2.26 5.48-4.78 7.18l7.73 6c4.51-4.18 7.09-10.36 7.09-17.65z'/%3E%3Cpath fill='%23FBBC05' d='M10.53 28.59c-.48-1.45-.76-2.99-.76-4.59s.27-3.14.76-4.59l-7.98-6.19C.92 16.46 0 20.12 0 24c0 3.88.92 7.54 2.56 10.78l7.97-6.19z'/%3E%3Cpath fill='%2334A853' d='M24 48c6.48 0 11.93-2.13 15.89-5.81l-7.73-6c-2.15 1.45-4.92 2.3-8.16 2.3-6.26 0-11.57-4.22-13.47-9.91l-7.98 6.19C6.51 42.62 14.62 48 24 48z'/%3E%3C/svg%3E");
    }
    div[data-testid="stColumn"]:first-child div[data-testid="stLinkButton"] > a:hover {
        background-color: #FFFDF7 !important;
        color: #1F1F1F !important;
        border-color: #E5C158 !important;
    }

    .landing-credit {
        border-top: 1px solid rgba(212, 175, 55, 0.35);
        padding-top: 10px;
        margin-top: 6px;
        font-size: 0.84rem;
        color: #E5D7C1;
        text-align: center;
    }
    .landing-credit span {
        color: #E5C158;
        font-weight: bold;
    }

    /* Right Column: Equal-Height Print-Style Digital Broadsheet */
    .newsprint-sheet {
        background-color: #FBF9F4;
        border: 2px solid #1D120A;
        border-radius: 12px;
        padding: 18px 22px;
        color: #1D120A;
        box-shadow: 0 6px 20px rgba(29, 18, 10, 0.08);
        height: 100%;
        min-height: 560px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        box-sizing: border-box;
    }
    .newsprint-masthead {
        border-bottom: 3px double #1D120A;
        padding-bottom: 8px;
        margin-bottom: 12px;
        text-align: center;
    }
    .newsprint-edition-bar {
        display: flex;
        justify-content: space-between;
        font-size: 0.72rem;
        font-weight: bold;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        color: #5C4938;
        border-bottom: 1px solid #C8BFA8;
        padding-bottom: 4px;
        margin-bottom: 6px;
    }
    .newsprint-paper-title {
        font-family: "Playfair Display", "Times New Roman", serif !important;
        font-size: 1.55rem;
        font-weight: 800;
        letter-spacing: 0.06em;
        color: #3C0612;
        margin: 0;
        line-height: 1.1;
    }
    .newsprint-paper-sub {
        font-size: 0.82rem;
        font-style: italic;
        color: #4A3B2C;
        margin-top: 3px;
    }

    /* Print Newspaper Lead Story + 2-Column Below Fold */
    .paper-lead-story {
        border-bottom: 1.5px solid #1D120A;
        padding-bottom: 12px;
        margin-bottom: 12px;
    }
    .paper-kicker {
        font-size: 0.69rem;
        font-weight: bold;
        letter-spacing: 0.04em;
        color: #7A1C24;
        margin-bottom: 3px;
    }
    .paper-corrob-badge {
        background-color: #EFE9DA;
        color: #3C0612;
        border: 1px solid #B8A98E;
        padding: 1px 5px;
        border-radius: 3px;
        font-size: 0.65rem;
    }
    .paper-lead-headline {
        font-family: "Playfair Display", "Times New Roman", serif !important;
        font-size: 1.18rem;
        font-weight: 700;
        color: #1D120A;
        margin: 0 0 3px 0;
        line-height: 1.25;
    }
    .paper-byline {
        font-size: 0.73rem;
        font-style: italic;
        color: #6B5846;
        margin-bottom: 5px;
    }
    .paper-lead-copy {
        font-size: 0.9rem;
        line-height: 1.44;
        color: #2B1E12;
        margin: 0;
    }
    .paper-columns-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 14px;
        align-items: start;
    }
    .paper-col-story:first-child {
        border-right: 1px solid #C8BFA8;
        padding-right: 12px;
    }
    .paper-col-headline {
        font-family: "Playfair Display", "Times New Roman", serif !important;
        font-size: 0.98rem;
        font-weight: 700;
        color: #1D120A;
        margin: 0 0 3px 0;
        line-height: 1.26;
    }
    .paper-col-copy {
        font-size: 0.85rem;
        line-height: 1.4;
        color: #33261A;
        margin: 0;
    }

    .newsprint-bottom-links {
        border-top: 2px solid #1D120A;
        margin-top: 14px;
        padding-top: 10px;
        text-align: center;
        font-size: 0.84rem;
        display: flex;
        flex-wrap: wrap;
        justify-content: center;
        gap: 8px;
    }
    .newsprint-bottom-links a {
        color: #3C0612 !important;
        font-weight: bold;
        text-decoration: underline;
    }

    /* ---------------------------------------------------------
       SIGNED-IN PORTAL HERO & READER CARDS
       --------------------------------------------------------- */
    .hero-wrapper {
        display: flex;
        align-items: stretch;
        width: 100%;
        height: 195px;
        margin-bottom: 14px;
        border-radius: 12px;
        overflow: hidden;
        border: 2px solid #D4AF37;
        background: linear-gradient(135deg, #3C0612 0%, #0B2545 100%);
    }
    .hero-logo {
        height: 195px;
        width: 195px;
        object-fit: cover;
        display: block;
        flex-shrink: 0;
        border-right: 2px solid #D4AF37;
    }
    .hero-banner-content {
        flex: 1;
        padding: 20px 28px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        color: #FFFFFF;
    }
    .hero-dateline-strip {
        font-size: 0.85rem;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: #F8E7B4;
        margin-bottom: 6px;
        font-weight: bold;
    }
    .hero-welcome {
        color: #E5C158;
        font-size: 1.9rem;
        font-weight: bold;
        margin: 0 0 8px 0;
        line-height: 1.2;
    }
    .hero-subtext {
        color: #F8E7B4;
        font-size: 1.02rem;
        margin: 0;
    }

    /* Native Streamlit Buttons & Link Buttons (Signed-In & Legal Views) */
    div.stButton > button,
    div[data-testid="stLinkButton"] > a {
        background-color: #3C0612 !important;
        color: #FFFFFF !important;
        border: 1.5px solid #D4AF37 !important;
        font-family: "Times New Roman", serif !important;
        font-weight: bold !important;
        font-size: 0.98rem !important;
        border-radius: 6px !important;
        padding: 0.42rem 1.15rem !important;
        text-decoration: none !important;
    }
    div.stButton > button:hover,
    div[data-testid="stLinkButton"] > a:hover {
        background-color: #590B1D !important;
        color: #E5C158 !important;
    }

    /* Reader Portal Briefing Cards */
    .cruxly-card {
        background-color: #FBF9F4;
        border: 1.5px solid #C8BFA8;
        border-left: 4px solid #3C0612;
        border-radius: 8px;
        padding: 18px 22px;
        margin-bottom: 10px;
        color: #1D120A;
        box-shadow: 0 2px 8px rgba(29, 18, 10, 0.05);
    }
    .cruxly-card-meta {
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        gap: 8px;
        margin-bottom: 10px;
        border-bottom: 1px solid #E2DAC8;
        padding-bottom: 8px;
    }
    .badge-tag {
        display: inline-block;
        background-color: #EFE9DA;
        color: #3C0612;
        border: 1px solid #B8A98E;
        padding: 2px 10px;
        border-radius: 4px;
        font-size: 0.82rem;
        font-weight: bold;
    }
    .cruxly-dateline {
        margin-left: auto;
        font-size: 0.85rem;
        color: #5C4938;
        font-style: italic;
    }

    /* Bilingual Side-by-Side Grid & Bengali Typography */
    .cruxly-bilingual-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 22px;
        align-items: start;
    }
    .cruxly-headline-en {
        font-family: "Playfair Display", "Times New Roman", serif !important;
        color: #1D120A;
        margin: 0 0 8px 0;
        font-size: 1.28rem;
        font-weight: 700;
        line-height: 1.32;
    }
    .cruxly-body-en {
        font-size: 1.03rem;
        line-height: 1.55;
        color: #2B1E12;
        margin: 0;
    }
    .cruxly-headline-bn {
        font-family: "Noto Serif Bengali", "Times New Roman", serif !important;
        color: #1D120A;
        margin: 0 0 8px 0;
        font-size: 1.24rem;
        font-weight: 700;
        line-height: 1.42;
    }
    .cruxly-body-bn {
        font-family: "Noto Serif Bengali", "Times New Roman", serif !important;
        font-size: 1.02rem;
        line-height: 1.65;
        color: #2B1E12;
        margin: 0;
    }

    /* Multi-Source Newspaper Reference Pills */
    .cruxly-ref-row {
        margin-top: 12px;
        padding-top: 10px;
        border-top: 1px dashed #C8BFA8;
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        gap: 7px;
    }
    .cruxly-ref-label {
        font-size: 0.88rem;
        font-weight: bold;
        color: #3C0612;
    }
    a.cruxly-ref-pill {
        display: inline-block;
        background-color: #FFFFFF;
        color: #0B2545 !important;
        border: 1px solid #8C7B65;
        border-radius: 4px;
        padding: 2px 9px;
        font-size: 0.84rem;
        font-weight: 600;
        text-decoration: none !important;
    }
    a.cruxly-ref-pill:hover {
        background-color: #3C0612;
        color: #FFFFFF !important;
        border-color: #3C0612;
    }

    /* Footer */
    .cruxly-footer {
        margin-top: 28px;
        padding: 16px 20px;
        background-color: #EFE9DA;
        border-top: 2px solid #3C0612;
        border-radius: 6px;
        font-size: 0.94rem;
        color: #1D120A;
        text-align: center;
        line-height: 1.6;
    }
    .cruxly-footer a {
        color: #3C0612;
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
        .cruxly-bilingual-grid,
        .paper-columns-grid {
            grid-template-columns: 1fr;
            gap: 12px;
        }
        .paper-col-story:first-child {
            border-right: none;
            border-bottom: 1px solid #C8BFA8;
            padding-right: 0;
            padding-bottom: 10px;
        }
        .newsprint-sheet {
            min-height: auto;
        }
        .cruxly-dateline {
            margin-left: 0;
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
# 3. PUBLIC LEGAL & POLICY PAGES (?page=charter / privacy / terms / guidelines)
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
    today_ist_str = datetime.now(IST).strftime("%A, %d %B %Y • IST Edition")
    st.markdown(
        f'<div class="hero-wrapper">'
        f'<img src="data:image/jpeg;base64,{logo_b64}" class="hero-logo" alt="Cruxly Logo" />'
        f'<div class="hero-banner-content">'
        f'<div class="hero-dateline-strip">{today_ist_str}</div>'
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
            <a href="?page=charter">Editorial Charter</a> |
            <a href="?page=terms">Copyright, Attribution &amp; Terms</a> |
            <a href="?page=privacy">Privacy Policy</a> |
            <a href="?page=guidelines">Reader Guidelines</a>
        </div>
        """,
        unsafe_allow_html=True,
    )
