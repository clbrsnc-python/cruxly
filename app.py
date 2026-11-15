import base64
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
# 3. PUBLIC LEGAL & POLICY PAGES (?page=privacy / ?page=terms)
# ---------------------------------------------------------
query_params = st.query_params
active_page = query_params.get("page")

if active_page == "privacy":
    st.markdown(
        f'<div class="hero-wrapper">'
        f'<img src="data:image/jpeg;base64,{logo_b64}" class="hero-logo" alt="Cruxly Logo" />'
        f'<div class="hero-banner-content">'
        f'<div class="hero-welcome">Cruxly — Privacy Policy &amp; Data Protection</div>'
        f'<p class="hero-subtext">Transparency on Google account sign-in and reader data storage.</p>'
        f'</div>'
        f'</div>',
        unsafe_allow_html=True,
    )
    st.link_button("← Back to Cruxly Home", url="?")
    st.markdown(
        """
        <div class="cruxly-card" style="margin-top: 14px;">
            <h3>1. Purpose of Cruxly</h3>
            <p><strong>Cruxly</strong> (<em>Read deeper. Faster.</em>) is a personalised news intelligence platform that collects and cross-verifies public reports from selected English, Bengali, and Hindi newspapers to deliver original consolidated abridged summaries in English and Bengali with direct links to original reporting.</p>
            <h3>2. Google Account Information Collected</h3>
            <p>When you sign in with Google, Cruxly receives only your basic Google profile identity:</p>
            <ul>
                <li><strong>Email Address (Gmail):</strong> Used as your unique login identifier and to communicate account approval status.</li>
                <li><strong>Display Name:</strong> Used to identify your registration request during administrator review.</li>
            </ul>
            <h3>3. How Your Data Is Used &amp; Protected</h3>
            <ul>
                <li>Your personal information is never sold, rented, or shared with third-party advertisers.</li>
                <li>All reader accounts require manual administrator approval before full portal access is granted.</li>
                <li>Reading preferences (selected state, topic priorities, excluded sources) and saved bookmarks are stored securely with strict row-level access controls so only you can access your personal settings.</li>
            </ul>
            <h3>4. Contact &amp; Data Removal</h3>
            <p>Registered readers may request account removal or data deletion at any time by contacting the Cruxly Administrator.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.stop()

if active_page == "terms":
    st.markdown(
        f'<div class="hero-wrapper">'
        f'<img src="data:image/jpeg;base64,{logo_b64}" class="hero-logo" alt="Cruxly Logo" />'
        f'<div class="hero-banner-content">'
        f'<div class="hero-welcome">Cruxly — Copyright, Publisher Attribution &amp; Terms of Use</div>'
        f'<p class="hero-subtext">Editorial safeguards, fair-dealing attribution, and original journalism support.</p>'
        f'</div>'
        f'</div>',
        unsafe_allow_html=True,
    )
    st.link_button("← Back to Cruxly Home", url="?")
    st.markdown(
        """
        <div class="cruxly-card" style="margin-top: 14px;">
            <h3>1. Copyright &amp; Fair-Dealing Compliance</h3>
            <ul>
                <li><strong>Original Abridged Summaries Only:</strong> Cruxly creates original, independent consolidated summaries and original translations in English and Bengali. Cruxly never republishes full newspaper articles, e-papers, or substantial verbatim excerpts.</li>
                <li><strong>Direct Publisher Attribution:</strong> Every consolidated report provides direct links and clear attribution to the original reporting newspapers so readers can read full articles on the publishers' official websites.</li>
                <li><strong>Image Policy:</strong> Unauthorised newspaper photographs are never reproduced. Images are displayed only when rights-cleared or properly licensed.</li>
                <li><strong>Temporary Source Text Removal:</strong> Any temporary extracted source text used for cross-verification is deleted immediately after processing and verification.</li>
            </ul>
            <h3>2. Editorial Standards &amp; Sensitive News Safeguards</h3>
            <ul>
                <li>Reports separate verified facts, important details, attributed viewpoints, and next steps.</li>
                <li>Sensitive stories require corroboration from at least five genuinely independent newspapers alongside central-fact verification before publication.</li>
            </ul>
            <h3>3. Support Original Journalism</h3>
            <p>Attribution and abridged synthesis are provided for informational news intelligence and do not substitute for full newspaper subscriptions. Readers are encouraged to support journalism by purchasing original newspaper editions.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.stop()

# ---------------------------------------------------------
# 4. OAUTH CALLBACK HANDLER (PKCE / CODE EXCHANGE)
# ---------------------------------------------------------
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
# 5. PUBLIC HOMEPAGE / LOGIN GATE (DPR v1.1 Sections 1, 2, 8, 11)
# ---------------------------------------------------------
if not user:
    oauth_url = None
    oauth_err = None
    try:
        redirect_url = st.secrets.get("APP_REDIRECT_URL", "https://cruxly.streamlit.app")
        res = supabase.auth.sign_in_with_oauth(
            {
                "provider": "google",
                "options": {"redirect_to": redirect_url},
            }
        )
        if res and res.url:
            oauth_url = res.url
    except Exception as exc:
        oauth_err = str(exc)

    # Flush Hero Header
    st.markdown(
        f'<div class="hero-wrapper">'
        f'<img src="data:image/jpeg;base64,{logo_b64}" class="hero-logo" alt="Cruxly Logo" />'
        f'<div class="hero-banner-content">'
        f'<div class="hero-welcome">Welcome to Cruxly — Intelligent News for Intelligent Readers.</div>'
        f'<p class="hero-subtext">Multi-source consolidated news intelligence in English &amp; Bengali.</p>'
        f'</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # Native Streamlit Link Button (opens Google OAuth cleanly outside sandboxed iframe)
    if oauth_url:
        st.link_button("Sign in with Google", url=oauth_url)
    else:
        st.error(f"Google Sign-In could not be initialized ({oauth_err or 'missing OAuth URL'}). Please check Streamlit Secrets.")

    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

    # DPR Section 1, 2 & 11: Core Promise, Access Policy & Copyright Transparency on Homepage
    col_about, col_access, col_legal = st.columns(3)
    with col_about:
        st.markdown(
            """
            <div class="cruxly-card">
                <h3>About Cruxly — Core Promise</h3>
                <p><strong>Cruxly</strong> (<em>Read deeper. Faster.</em>) cross-verifies reporting from 15 selected English, Bengali, and Hindi newspapers into original consolidated abridged summaries in English and Bengali.</p>
                <p>Understand essential facts across sources faster, and return to original reporting whenever deeper reading is needed.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col_access:
        st.markdown(
            """
            <div class="cruxly-card">
                <h3>Reader Registration &amp; Access</h3>
                <p><strong>Gmail Sign-In:</strong> Register or sign in using your Gmail account.</p>
                <p><strong>Administrator Approval:</strong> Protected access to full consolidated reports, scheduled editions (06:00 AM &amp; 06:00 PM IST), and the searchable archive requires administrator approval.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col_legal:
        st.markdown(
            """
            <div class="cruxly-card">
                <h3>Copyright &amp; Publisher Attribution</h3>
                <p><strong>Original Abridged Synthesis:</strong> Cruxly never reproduces full articles, e-papers, or unauthorised newspaper photos. Every report includes direct links to original publishers.</p>
                <p>Read full policies under <a href="?page=terms">Copyright &amp; Terms</a> and <a href="?page=privacy">Privacy Policy</a>.</p>
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

    # DPR Section 11 & 8: Discreet Footer with About/Terms, Privacy Policy & Original Edition Note
    st.markdown(
        """
        <div class="cruxly-footer">
            <strong>Cruxly — Read deeper. Faster.</strong> | Original abridged synthesis with direct attribution to original publishers.
            Readers are encouraged to support journalism by purchasing original newspaper editions.<br/>
            <a href="?page=terms">Copyright, Attribution &amp; Terms</a> |
            <a href="?page=privacy">Privacy Policy</a>
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
            <strong>Cruxly — Read deeper. Faster.</strong> | Readers are encouraged to support journalism by purchasing original newspaper editions.<br/>
            <a href="?page=terms">Copyright, Attribution &amp; Terms</a> |
            <a href="?page=privacy">Privacy Policy</a>
        </div>
        """,
        unsafe_allow_html=True,
    )
