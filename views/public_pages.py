from datetime import datetime
import html
from urllib.parse import quote
import pytz
import streamlit as st
from supabase import Client
from utils.supabase_client import get_pkce_pair

IST = pytz.timezone("Asia/Kolkata")

GOOGLE_G_SVG = """
<svg width="22" height="22" viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg" style="flex-shrink:0;">
  <path fill="#EA4335" d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5z"/>
  <path fill="#4285F4" d="M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.94c-.58 2.96-2.26 5.48-4.78 7.18l7.73 6c4.51-4.18 7.09-10.36 7.09-17.65z"/>
  <path fill="#FBBC05" d="M10.53 28.59c-.48-1.45-.76-2.99-.76-4.59s.27-3.14.76-4.59l-7.98-6.19C.92 16.46 0 20.12 0 24c0 3.88.92 7.54 2.56 10.78l7.97-6.19z"/>
  <path fill="#34A853" d="M24 48c6.48 0 11.93-2.13 15.89-5.81l-7.73-6c-2.15 1.45-4.92 2.3-8.16 2.3-6.26 0-11.57-4.22-13.47-9.91l-7.98 6.19C6.51 42.62 14.62 48 24 48z"/>
</svg>
""".strip()


def _format_ist_short(raw_iso: str | None) -> str:
    if not raw_iso:
        return ""
    try:
        dt = datetime.fromisoformat(raw_iso.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = pytz.UTC.localize(dt)
        return dt.astimezone(IST).strftime("%d %b %Y, %I:%M %p IST")
    except Exception:
        return str(raw_iso)[:16]


def render_legal_page(active_page: str, logo_b64: str) -> bool:
    """Renders ?page=charter, ?page=privacy, ?page=terms, or ?page=guidelines. Returns True if rendered."""
    legal_pages = {
        "charter": (
            "Cruxly — Editorial Charter",
            "Multi-source cross-verification, fact-first synthesis, and journalistic integrity.",
            """
            <h3>1. Our Core Editorial Promise</h3>
            <p><strong>Cruxly</strong> (<em>Read deeper. Faster.</em>) aggregates and cross-verifies public reporting from selected English, Bengali, and Hindi newspapers into concise, original abridged briefings.</p>
            <h3>2. Verification &amp; Synthesis Standards</h3>
            <ul>
                <li><strong>Multi-Source Clustering:</strong> Related coverage across multiple newspapers is merged into a single unified briefing so readers get the full picture without repetition.</li>
                <li><strong>Fact-First Separation:</strong> Reports clearly distinguish verified facts, essential context, attributed viewpoints, and next steps.</li>
                <li><strong>Sensitive News Corroboration:</strong> Sensitive stories undergo multi-source corroboration across independent outlets before publication.</li>
                <li><strong>Original Journalism Support:</strong> Every briefing links directly to original publishers so readers can read full coverage on official newspaper websites.</li>
            </ul>
            """,
        ),
        "privacy": (
            "Cruxly — Privacy Policy & Data Protection",
            "Transparency on Google account sign-in and reader data storage.",
            """
            <h3>1. Google Account Information Collected</h3>
            <p>When you sign in with Google, Cruxly receives only your basic Google profile identity:</p>
            <ul>
                <li><strong>Email Address (Gmail):</strong> Used strictly as your unique sign-in identifier and to communicate account approval status.</li>
                <li><strong>Display Name:</strong> Used solely to identify your registration request during administrator review.</li>
            </ul>
            <h3>2. How Your Data Is Used &amp; Protected</h3>
            <ul>
                <li>Your personal information is never sold, rented, or shared with third-party advertisers.</li>
                <li>All reader accounts require manual administrator approval before full portal access is granted.</li>
                <li>Saved stories and personal preferences are isolated under strict PostgreSQL Row-Level Security (RLS) so only you can view or modify your bookmarks.</li>
            </ul>
            <h3>3. Contact &amp; Data Removal</h3>
            <p>Registered readers may request account removal or full data deletion at any time by contacting the Cruxly Administrator.</p>
            """,
        ),
        "terms": (
            "Cruxly — Copyright, Publisher Attribution & Terms of Use",
            "Fair-dealing compliance, direct publisher attribution, and original journalism support.",
            """
            <h3>1. Copyright &amp; Fair-Dealing Compliance</h3>
            <ul>
                <li><strong>Original Abridged Summaries Only:</strong> Cruxly creates original, independent consolidated summaries and original translations in English and Bengali. Full newspaper articles, e-papers, and substantial verbatim excerpts are never republished.</li>
                <li><strong>Direct Publisher Attribution:</strong> Every consolidated briefing provides clickable source links and clear attribution to original reporting newspapers.</li>
                <li><strong>Zero Unauthorised Media:</strong> Unauthorised newspaper photographs are never reproduced or hosted.</li>
                <li><strong>Transient Source Text Removal:</strong> Temporary extracted snippets used for cross-verification are discarded immediately after processing.</li>
            </ul>
            <h3>2. Support Original Journalism</h3>
            <p>Abridged synthesis is provided for informational news intelligence and does not substitute for newspaper subscriptions. Readers are encouraged to support journalism by purchasing original newspaper editions.</p>
            """,
        ),
        "guidelines": (
            "Cruxly — Reader Guidelines",
            "How registration, bilingual reading modes, and personal bookmarks work.",
            """
            <h3>Getting Started on Cruxly</h3>
            <ol>
                <li><strong>Sign In with Google:</strong> Use the <em>Sign in with Google</em> button on the front page to authenticate securely with your Gmail account.</li>
                <li><strong>Administrator Review:</strong> New reader accounts are reviewed by an administrator to maintain a reliable, spam-free editorial platform.</li>
                <li><strong>Bilingual Reading Modes:</strong> Once approved, switch effortlessly between <em>Bilingual (Side-by-Side)</em>, <em>English</em>, and <em>Bengali</em> views.</li>
                <li><strong>Filter &amp; Bookmark:</strong> Browse by Edition, Geography, or Genre, and save important stories to your personal <em>Saved News</em> shelf.</li>
            </ol>
            """,
        ),
    }

    if active_page in legal_pages:
        title, subtitle, body_html = legal_pages[active_page]
        st.markdown(
            f'<div class="hero-wrapper">'
            f'<img src="data:image/jpeg;base64,{logo_b64}" class="hero-logo" alt="Cruxly Logo" />'
            f'<div class="hero-banner-content">'
            f'<div class="hero-welcome">{title}</div>'
            f'<p class="hero-subtext">{subtitle}</p>'
            f'</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
        st.link_button("← Back to Cruxly Front Page", url="?")
        st.markdown(
            f'<div class="cruxly-card" style="margin-top: 14px;">{body_html}</div>',
            unsafe_allow_html=True,
        )
        return True

    return False


def _select_front_page_stories(supabase: Client) -> list[dict]:
    """
    Fetches recent published stories and prioritizes at least 2 multi-source corroborated stories
    (>= 2 distinct newspaper references) so the front page showcases genuine cross-verification.
    """
    try:
        res = (
            supabase.table("stories")
            .select(
                "id, headline_en, primary_genre, geography, summary_en, published_at, "
                "story_references(source_name, article_url)"
            )
            .eq("status", "published")
            .order("published_at", desc=True)
            .limit(35)
            .execute()
        )
        rows = res.data or []
    except Exception:
        return []

    corroborated: list[dict] = []
    single_source: list[dict] = []

    for row in rows:
        refs = row.get("story_references") or []
        distinct_sources = {
            (r.get("source_name") or "").strip()
            for r in refs
            if (r.get("source_name") or "").strip()
        }
        row["_source_count"] = len(distinct_sources) if distinct_sources else len(refs)
        if row["_source_count"] >= 2:
            corroborated.append(row)
        else:
            single_source.append(row)

    # Guarantee at least 2 corroborated stories first, then fill up to 3 total stories (1 lead + 2 columns)
    selected: list[dict] = []
    selected.extend(corroborated[:3])
    if len(selected) < 3:
        selected.extend(single_source[: 3 - len(selected)])
    return selected[:3]


def render_public_landing(supabase: Client, logo_b64: str) -> None:
    """Renders the split-screen broadsheet landing page: left branding + Google OAuth, right print-newspaper front page."""
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

    today_ist = datetime.now(IST).strftime("%A, %d %B %Y")
    left_col, right_col = st.columns([1.0, 1.3], gap="large")

    # ---------------------------------------------------------
    # LEFT COLUMN: ENLARGED CRUXLY LOGO + MULTICOLOR GOOGLE SIGN-IN
    # ---------------------------------------------------------
    with left_col:
        st.markdown(
            f"""
            <div class="landing-brand-panel">
                <img src="data:image/jpeg;base64,{logo_b64}" class="landing-logo-img" alt="Cruxly Logo" />
                <p class="landing-subtitle">
                    An intelligent bilingual abridged newspaper service from leading English, Bengali, and Hindi dailies.
                </p>
                <div class="landing-feature-pill">📰 Available in Morning &amp; Evening Edition</div>
                <div class="landing-feature-pill">🔄 Multi-Source Cross-Referencing &amp; Clustering</div>
                <div class="landing-feature-pill">🌐 Bilingual English &amp; Bengali Briefings</div>
                <div class="landing-google-wrap">
                    <a href="{oauth_url}" target="_self" class="google-signin-btn">
                        {GOOGLE_G_SVG}
                        <span>Sign in with Google</span>
                    </a>
                </div>
                <div class="landing-credit">
                    Designed &amp; Crafted by: <span>Dr Joydip Chandra</span> | &copy; 2026 Cruxly
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # ---------------------------------------------------------
    # RIGHT COLUMN: PRINT-STYLE BROADSHEET FRONT PAGE + POLICY LINKS
    # ---------------------------------------------------------
    with right_col:
        previews = _select_front_page_stories(supabase)

        def _build_article_block(item: dict, is_lead: bool) -> str:
            headline = html.escape(item.get("headline_en") or "Untitled Briefing")
            genre = html.escape(item.get("primary_genre") or "General")
            geo = html.escape(item.get("geography") or "National")
            dateline = html.escape(_format_ist_short(item.get("published_at")))
            src_count = item.get("_source_count", 1)
            corrob_tag = (
                f' &bull; <span class="paper-corrob-badge">VERIFIED ACROSS {src_count} DAILIES</span>'
                if src_count >= 2
                else ""
            )

            sum_obj = item.get("summary_en") or {}
            raw_brief = (
                sum_obj.get("in_brief")
                or sum_obj.get("what_happened")
                or "Sign in with Google to read the complete consolidated briefing and original newspaper links."
            ) if isinstance(sum_obj, dict) else str(sum_obj)

            max_len = 230 if is_lead else 165
            brief_text = html.escape(raw_brief[:max_len] + ("..." if len(raw_brief) > max_len else ""))

            if is_lead:
                return (
                    f'<article class="paper-lead-story">'
                    f'<div class="paper-kicker">{genre.upper()} &bull; {geo.upper()}{corrob_tag}</div>'
                    f'<h2 class="paper-lead-headline">{headline}</h2>'
                    f'<div class="paper-byline">{dateline}</div>'
                    f'<p class="paper-lead-copy">{brief_text}</p>'
                    f'</article>'
                )
            return (
                f'<article class="paper-col-story">'
                f'<div class="paper-kicker">{genre.upper()}{corrob_tag}</div>'
                f'<h3 class="paper-col-headline">{headline}</h3>'
                f'<div class="paper-byline">{geo} &bull; {dateline}</div>'
                f'<p class="paper-col-copy">{brief_text}</p>'
                f'</article>'
            )

        if previews:
            lead_html = _build_article_block(previews[0], is_lead=True)
            cols_html = ""
            if len(previews) > 1:
                sub_blocks = "".join(_build_article_block(p, is_lead=False) for p in previews[1:3])
                cols_html = f'<div class="paper-columns-grid">{sub_blocks}</div>'
            front_body_html = lead_html + cols_html
        else:
            front_body_html = (
                '<article class="paper-lead-story">'
                '<div class="paper-kicker">FRONT PAGE EDITION</div>'
                '<h2 class="paper-lead-headline">Latest Consolidated Briefings</h2>'
                '<p class="paper-lead-copy">Sign in with Google on the left to access the full bilingual news archive and original newspaper links.</p>'
                '</article>'
            )

        st.markdown(
            f"""
            <div class="newsprint-sheet">
                <div class="newsprint-masthead">
                    <div class="newsprint-edition-bar">
                        <span>DIGITAL BROADSHEET</span>
                        <span>{today_ist}</span>
                    </div>
                    <div class="newsprint-paper-title">THE CRUXLY DISPATCH</div>
                    <div class="newsprint-paper-sub">Cross-Verified Front-Page Briefings &bull; Sign in for Full Bilingual Reports &amp; Source Links</div>
                </div>
                {front_body_html}
                <div class="newsprint-bottom-links">
                    <a href="?page=charter">Editorial Charter</a>
                    <span>&bull;</span>
                    <a href="?page=privacy">Privacy Policy</a>
                    <span>&bull;</span>
                    <a href="?page=terms">Copyright &amp; Terms</a>
                    <span>&bull;</span>
                    <a href="?page=guidelines">Reader Guidelines</a>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
