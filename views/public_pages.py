from datetime import datetime
import html
import re
from urllib.parse import quote
import pytz
import streamlit as st
from supabase import Client
from utils.supabase_client import get_pkce_pair

IST = pytz.timezone("Asia/Kolkata")


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


def _clean_preview_summary(raw_text: str) -> str:
    """Removes inline corroboration parentheticals for clean front-page excerpts."""
    cleaned = re.sub(r"\s*\(Corroborated across[^)]*\)\.?", "", raw_text, flags=re.IGNORECASE)
    return cleaned.strip()


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
    """Fetches 3 recent published stories across diverse genres for a balanced front-page layout."""
    try:
        res = (
            supabase.table("stories")
            .select("id, headline_en, primary_genre, geography, summary_en, published_at")
            .eq("status", "published")
            .order("published_at", desc=True)
            .limit(15)
            .execute()
        )
        rows = res.data or []
    except Exception:
        return []

    picked: list[dict] = []
    seen_genres: set[str] = set()
    for r in rows:
        g = (r.get("primary_genre") or "").strip()
        if g not in seen_genres:
            picked.append(r)
            seen_genres.add(g)
        if len(picked) == 3:
            break

    if len(picked) < 3:
        picked_ids = {p["id"] for p in picked}
        for r in rows:
            if r["id"] not in picked_ids:
                picked.append(r)
            if len(picked) == 3:
                break

    return picked[:3]


def render_public_landing(supabase: Client, logo_b64: str) -> None:
    """Renders the equal-height split-screen broadsheet landing page with native top-frame Google OAuth."""
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
    left_col, right_col = st.columns([1.0, 1.32], gap="large")

    # ---------------------------------------------------------
    # LEFT COLUMN: ENLARGED LOGO + 5 BOXES + GOOGLE OAUTH + CREDIT + POLICY LINKS
    # ---------------------------------------------------------
    with left_col:
        with st.container(border=True):
            st.markdown(
                f"""
                <div class="brand-top-block">
                    <img src="data:image/jpeg;base64,{logo_b64}" class="landing-logo-img" alt="Cruxly Logo" />
                    <div class="landing-feature-pill">✨ Intelligent Bilingual News Briefings</div>
                    <div class="landing-feature-pill">🗞️ Curated from English, Bengali &amp; Hindi Dailies</div>
                    <div class="landing-feature-pill">📰 Available in Morning &amp; Evening Edition</div>
                    <div class="landing-feature-pill">🔄 Multi-Source Cross-Referencing &amp; Clustering</div>
                    <div class="landing-feature-pill">🌐 Direct Attribution Links to Original Publishers</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            st.link_button("Sign in with Google", url=oauth_url, use_container_width=True)

            st.markdown(
                """
                <div class="landing-credit">
                    Designed &amp; Crafted by: <span>Dr Joydip Chandra</span> | &copy; 2026 Cruxly
                </div>
                <div class="landing-policy-links">
                    <a href="?page=charter">Editorial Charter</a>
                    <span>&bull;</span>
                    <a href="?page=privacy">Privacy Policy</a>
                    <span>&bull;</span>
                    <a href="?page=terms">Copyright &amp; Terms</a>
                    <span>&bull;</span>
                    <a href="?page=guidelines">Reader Guidelines</a>
                </div>
                """,
                unsafe_allow_html=True,
            )

    # ---------------------------------------------------------
    # RIGHT COLUMN: PURE PRINT-STYLE DIGITAL BROADSHEET
    # ---------------------------------------------------------
    with right_col:
        previews = _select_front_page_stories(supabase)

        def _build_article_block(item: dict, is_lead: bool) -> str:
            headline = html.escape(item.get("headline_en") or "Untitled Briefing")
            genre = html.escape(item.get("primary_genre") or "General")
            geo = html.escape(item.get("geography") or "National")
            dateline = html.escape(_format_ist_short(item.get("published_at")))

            sum_obj = item.get("summary_en") or {}
            raw_brief = (
                sum_obj.get("in_brief")
                or sum_obj.get("what_happened")
                or "Sign in with Google to read the complete consolidated briefing and original newspaper links."
            ) if isinstance(sum_obj, dict) else str(sum_obj)
            clean_brief = _clean_preview_summary(raw_brief)

            max_len = 220 if is_lead else 175
            brief_text = html.escape(clean_brief[:max_len] + ("..." if len(clean_brief) > max_len else ""))

            if is_lead:
                return (
                    f'<article class="paper-lead-story">'
                    f'<div class="paper-kicker">{genre.upper()} &bull; {geo.upper()}</div>'
                    f'<h2 class="paper-lead-headline">{headline}</h2>'
                    f'<div class="paper-byline">{dateline}</div>'
                    f'<p class="paper-lead-copy">{brief_text}</p>'
                    f'</article>'
                )
            return (
                f'<article class="paper-col-story">'
                f'<div class="paper-kicker">{genre.upper()}</div>'
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
                    <div class="newsprint-paper-sub">Front-Page Briefings &bull; Sign in for Full Bilingual Reports &amp; Source Links</div>
                </div>
                {front_body_html}
            </div>
            """,
            unsafe_allow_html=True,
        )
