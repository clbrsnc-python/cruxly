from urllib.parse import quote
import streamlit as st
from supabase import Client
from utils.supabase_client import get_pkce_pair


def render_legal_page(active_page: str, logo_b64: str) -> bool:
    """Renders ?page=privacy or ?page=terms if requested. Returns True if rendered."""
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
        return True

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
        return True

    return False


def render_public_landing(supabase: Client, logo_b64: str) -> None:
    """Renders the public homepage and Google OAuth login gate."""
    _, code_challenge = get_pkce_pair()
    base_url = st.secrets["SUPABASE_URL"].rstrip("/")
    redirect_url = st.secrets.get("APP_REDIRECT_URL", "https://cruxly.streamlit.app")
    oauth_url = (
        f"{base_url}/auth/v1/authorize"
        f"?provider=google"
        f"&redirect_to={quote(redirect_url, safe='')}"
        f"&code_challenge={code_challenge}"
        f"&code_challenge_method=S256"
    )

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

    st.link_button("Sign in with Google", url=oauth_url)
    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

    col_about, col_access, col_legal = st.columns(3)
    with col_about:
        st.markdown(
            """
            <div class="cruxly-card">
                <h3>About Cruxly — Core Promise</h3>
                <p><strong>Cruxly</strong> (<em>Read deeper. Faster.</em>) cross-verifies reporting from selected English, Bengali, and Hindi newspapers into original consolidated abridged summaries in English and Bengali.</p>
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
            short_preview = summary_obj.get(
                "what_happened",
                "Sign in with an approved account to read the full consolidated report.",
            )
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
