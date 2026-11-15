import base64
from urllib.parse import quote
import streamlit as st
from supabase import create_client, Client

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

# Single-line SVG data URI so Streamlit Markdown never breaks HTML tags
GOOGLE_ICON_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 48 48">'
    '<path fill="#EA4335" d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5z"/>'
    '<path fill="#4285F4" d="M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.94c-.58 2.96-2.26 5.48-4.78 7.18l7.73 6c4.51-4.18 7.09-10.36 7.09-17.65z"/>'
    '<path fill="#FBBC05" d="M10.53 28.59c-.48-1.45-.76-2.99-.76-4.59s.27-3.14.76-4.59l-7.98-6.19C.92 16.46 0 20.12 0 24c0 3.88.92 7.54 2.56 10.78l7.97-6.19z"/>'
    '<path fill="#34A853" d="M24 48c6.48 0 11.93-2.13 15.89-5.81l-7.73-6c-2.15 1.45-4.92 2.3-8.16 2.3-6.26 0-11.57-4.22-13.47-9.91l-7.98 6.19C6.51 42.62 14.62 48 24 48z"/>'
    '</svg>'
)
GOOGLE_ICON_URI = f"data:image/svg+xml;utf8,{quote(GOOGLE_ICON_SVG)}"

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
        margin-bottom: 22px;
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
        margin: 0 0 18px 0;
        line-height: 1.25;
    }

    /* Official Multicolor Google Sign-In Button */
    a.google-btn {
        display: inline-flex;
        align-items: center;
        gap: 12px;
        background-color: #FFFFFF;
        color: #1F1F1F !important;
        text-decoration: none !important;
        font-family: "Times New Roman", Times, serif !important;
        font-weight: bold;
        font-size: 1.1rem;
        padding: 10px 22px;
        border-radius: 6px;
        border: 2px solid #D4AF37;
        width: fit-content;
        transition: none !important;
        animation: none !important;
    }
    a.google-btn:hover {
        background-color: #F8F9FA;
        color: #000000 !important;
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
    .cruxly-card p {
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

    /* Discreet Footer Note (DPR v1.1 Section 8 & 11) */
    .cruxly-footer {
        margin-top: 28px;
        padding: 14px 20px;
        background-color: #E8EEF5;
        border-top: 2px solid #1B4965;
        border-radius: 6px;
        font-size: 0.95rem;
        color: #102033;
        text-align: center;
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
        st.warning("Your sign-in session could not be verified. Please try signing in with Google again.")

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
# 4. PUBLIC HOMEPAGE / LOGIN GATE (DPR v1.1 Sections 1, 2, 8, 11)
# ---------------------------------------------------------
if not user:
    oauth_url = "#"
    try:
        redirect_url = st.secrets.get("APP_REDIRECT_URL", "http://localhost:8501")
        res = supabase.auth.sign_in_with_oauth(
            {
                "provider": "google",
                "options": {"redirect_to": redirect_url},
            }
        )
        if res and res.url:
            oauth_url = res.url
    except Exception:
        oauth_url = "#"

    # Flush Hero Header with Punctuated Welcome & Clean Multicolor Google Button
    st.markdown(
        f'<div class="hero-wrapper">'
        f'<img src="data:image/jpeg;base64,{logo_b64}" class="hero-logo" alt="Cruxly Logo" />'
        f'<div class="hero-banner-content">'
        f'<div class="hero-welcome">Welcome to Cruxly — Intelligent News for Intelligent Readers.</div>'
        f'<a href="{oauth_url}" target="_self" class="google-btn">'
        f'<img src="{GOOGLE_ICON_URI}" width="20" height="20" alt="Google" />'
        f'<span>Sign in with Google</span>'
        f'</a>'
        f'</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # DPR Section 1 & 2: Core Promise, Access Policy & Public Shared Headline Previews
    col_about, col_access = st.columns(2)
    with col_about:
        st.markdown(
            """
            <div class="cruxly-card">
                <h3>Core Editorial Promise</h3>
                <p>Read across sources, understand the essential facts faster, and return to original reporting whenever deeper reading is needed.</p>
                <p><strong>Languages:</strong> Consolidated reports in English and Bengali across 12 curated genres, with direct links to original newspapers.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col_access:
        st.markdown(
            """
            <div class="cruxly-card">
                <h3>Reader Registration &amp; Access Policy</h3>
                <p><strong>Sign-In:</strong> Register or sign in using your Gmail account.</p>
                <p><strong>Administrator Approval:</strong> Protected access to full consolidated reports, scheduled editions (06:00 AM &amp; 06:00 PM IST), and the searchable archive requires administrator approval.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # DPR Section 2: Public Homepage Shared Headlines & Short Original Abridged Previews
    st.markdown("### Public Headline Previews")
    try:
        preview_res = (
            supabase.table("stories")
            .select("id, headline_en, primary_genre, geography, summary_en, published_at")
            .eq("status", "published")
            .order("published_at", desc=True)
            .limit(3)
            .execute()
        )
        previews = preview_res.data or []
    except Exception:
        previews = []

    if previews:
        for item in previews:
            summary_obj = item.get("summary_en") or {}
            short_preview = summary_obj.get("what_happened", "Sign in with an approved account to read the full consolidated report.")
            st.markdown(
                f"""
                <div class="cruxly-card">
                    <span class="badge-tag">{item.get('primary_genre', 'News')} | {item.get('geography', 'National')}</span>
                    <h3>{item.get('headline_en', 'Untitled Report')}</h3>
                    <p>{short_preview}</p>
                    <p style="font-size: 0.9rem; color: #1B4965;"><em>Sign in with Google above to view full multi-source synthesis and original newspaper links.</em></p>
                </div>
                """,
                unsafe_allow_html=True,
            )
    else:
        st.markdown(
            """
            <div class="cruxly-card">
                <span class="badge-tag">Edition Schedule: 06:00 AM &amp; 06:00 PM IST</span>
                <h3>Latest Consolidated Briefings</h3>
                <p>Public headline previews will appear here once the first verified news cycle is published. Sign in with your Gmail account above to register for full reader access.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # DPR Section 11 & 8: Discreet Transparency & Original Edition Footer
    st.markdown(
        """
        <div class="cruxly-footer">
            <strong>Cruxly — Read deeper. Faster.</strong> | Original abridged synthesis with direct attribution to original publishers.
            Readers are encouraged to support journalism by purchasing original newspaper editions.
        </div>
        """,
        unsafe_allow_html=True,
    )

else:
    # Signed-In Header
    st.markdown(
        f'<div class="hero-wrapper">'
        f'<img src="data:image/jpeg;base64,{logo_b64}" class="hero-logo" alt="Cruxly Logo" />'
        f'<div class="hero-banner-content">'
        f'<div class="hero-welcome">Welcome to Cruxly — Intelligent News for Intelligent Readers.</div>'
        f'<div style="color: #F8E7B4; font-size: 1.05rem;">Signed in as: <strong>{user.email}</strong></div>'
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

    st.markdown(
        """
        <div class="cruxly-footer">
            <strong>Cruxly — Read deeper. Faster.</strong> | Readers are encouraged to support journalism by purchasing original newspaper editions.
        </div>
        """,
        unsafe_allow_html=True,
    )
