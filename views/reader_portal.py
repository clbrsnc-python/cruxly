from datetime import datetime
import html
import pytz
import streamlit as st
from supabase import Client

IST = pytz.timezone("Asia/Kolkata")
PAGE_SIZE = 25


def _extract_user_id(user_obj) -> str:
    """Safely extracts UUID string whether app.py passes user.id (str) or a Supabase User object."""
    if isinstance(user_obj, str):
        return user_obj
    return str(getattr(user_obj, "id", "") or "")


def _format_ist_timestamp(raw_iso: str | None) -> str:
    """Formats ISO timestamp into readable Indian Standard Time (IST) newspaper dateline."""
    if not raw_iso:
        return ""
    try:
        dt = datetime.fromisoformat(raw_iso.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = pytz.UTC.localize(dt)
        dt_ist = dt.astimezone(IST)
        return dt_ist.strftime("%d %b %Y, %I:%M %p IST")
    except Exception:
        return str(raw_iso)[:16]


def _fetch_saved_story_ids(supabase: Client, user_id: str) -> set[str]:
    """Loads the logged-in reader's bookmarked story IDs from public.saved_stories."""
    if not user_id:
        return set()
    try:
        res = (
            supabase.table("saved_stories")
            .select("story_id")
            .eq("user_id", user_id)
            .execute()
        )
        return {str(row["story_id"]) for row in (res.data or []) if row.get("story_id")}
    except Exception:
        return set()


def _toggle_save_story(supabase: Client, user_id: str, story_id: str, is_currently_saved: bool) -> None:
    """Adds or removes a bookmark in public.saved_stories."""
    if not user_id or not story_id:
        return
    try:
        if is_currently_saved:
            (
                supabase.table("saved_stories")
                .delete()
                .eq("user_id", user_id)
                .eq("story_id", story_id)
                .execute()
            )
        else:
            (
                supabase.table("saved_stories")
                .upsert({"user_id": user_id, "story_id": story_id}, on_conflict="user_id,story_id")
                .execute()
            )
    except Exception as exc:
        st.error(f"Could not update bookmark: {exc}")


def _fetch_active_genres(supabase: Client) -> list[str]:
    """Fetches active genre names for the reader filter dropdown."""
    try:
        res = (
            supabase.table("genres")
            .select("name_en")
            .eq("is_active", True)
            .order("id")
            .execute()
        )
        names = [r["name_en"] for r in (res.data or []) if r.get("name_en")]
        if names:
            return names
    except Exception:
        pass
    return [
        "Politics & Governance",
        "Education",
        "Science & Technology",
        "Business & Economy",
        "Health",
        "Sports",
        "Entertainment",
        "Environment & Climate",
        "Crime & Law",
        "Agriculture & Rural Affairs",
        "Career & Employment",
        "Culture & Literature",
    ]


def _fetch_stories_page(
    supabase: Client,
    edition_filter: str,
    geo_filter: str,
    genre_filter: str,
    search_query: str,
    limit_count: int,
) -> tuple[list[dict], int]:
    """
    Fetches published stories along with ALL linked Bengali, English, and Hindi newspaper references
    via relational embedding so multi-source links never get dropped.
    """
    select_cols = (
        "id, headline_en, headline_bn, primary_genre, secondary_genres, "
        "geography, state_name, edition_slot, summary_en, summary_bn, published_at, "
        "story_references(source_name, article_url, hindi_original_headline)"
    )
    query = (
        supabase.table("stories")
        .select(select_cols, count="exact")
        .eq("status", "published")
    )

    if edition_filter == "Morning Edition":
        query = query.eq("edition_slot", "morning")
    elif edition_filter == "Evening Edition":
        query = query.eq("edition_slot", "evening")

    if geo_filter != "All":
        query = query.eq("geography", geo_filter)

    if genre_filter != "All":
        query = query.eq("primary_genre", genre_filter)

    clean_q = (search_query or "").strip()
    if clean_q:
        safe_q = clean_q.replace(",", " ").replace("%", "")
        query = query.or_(f"headline_en.ilike.%{safe_q}%,headline_bn.ilike.%{safe_q}%")

    res = query.order("published_at", desc=True).range(0, max(limit_count - 1, 0)).execute()
    rows = res.data or []
    total_count = res.count if getattr(res, "count", None) is not None else len(rows)
    return rows, total_count


def _fetch_saved_stories_full(supabase: Client, saved_ids: set[str]) -> list[dict]:
    """Fetches full story cards and references for all bookmarked stories."""
    if not saved_ids:
        return []
    select_cols = (
        "id, headline_en, headline_bn, primary_genre, secondary_genres, "
        "geography, state_name, edition_slot, summary_en, summary_bn, published_at, "
        "story_references(source_name, article_url, hindi_original_headline)"
    )
    try:
        res = (
            supabase.table("stories")
            .select(select_cols)
            .in_("id", list(saved_ids))
            .order("published_at", desc=True)
            .execute()
        )
        return res.data or []
    except Exception:
        return []


def _render_story_card(
    supabase: Client,
    story: dict,
    lang_mode: str,
    user_id: str,
    saved_ids: set[str],
    key_prefix: str,
) -> None:
    """Renders an individual editorial briefing card with multi-language source links, Save, and Share."""
    sid = str(story["id"])
    is_saved = sid in saved_ids

    h_en = html.escape(story.get("headline_en") or "")
    h_bn = html.escape(story.get("headline_bn") or "")

    sum_en_obj = story.get("summary_en") or {}
    sum_bn_obj = story.get("summary_bn") or {}
    brief_en = html.escape(
        sum_en_obj.get("in_brief") if isinstance(sum_en_obj, dict) else str(sum_en_obj)
    )
    brief_bn = html.escape(
        sum_bn_obj.get("in_brief") if isinstance(sum_bn_obj, dict) else str(sum_bn_obj)
    )

    genre = html.escape(story.get("primary_genre") or "General")
    geo = html.escape(story.get("geography") or "National")
    state_name = story.get("state_name")
    geo_label = f"{geo} ({html.escape(state_name)})" if (geo == "State" and state_name) else geo
    slot_label = html.escape((story.get("edition_slot") or "live").upper())
    dateline = html.escape(_format_ist_timestamp(story.get("published_at")))

    refs = story.get("story_references") or []
    seen_urls: set[str] = set()
    unique_refs: list[dict] = []
    for r in refs:
        url = (r.get("article_url") or "").strip()
        if url and url not in seen_urls:
            seen_urls.add(url)
            unique_refs.append(r)

    ref_links_html = ""
    if unique_refs:
        pills = []
        for r in unique_refs:
            src_name = html.escape(r.get("source_name") or "Source")
            src_url = html.escape(r.get("article_url") or "#", quote=True)
            pills.append(
                f'<a href="{src_url}" target="_blank" rel="noopener noreferrer" '
                f'class="cruxly-ref-pill">{src_name} ↗</a>'
            )
        ref_links_html = (
            f'<div class="cruxly-ref-row">'
            f'<span class="cruxly-ref-label">Sources ({len(unique_refs)}):</span> '
            f'{"".join(pills)}'
            f'</div>'
        )

    if lang_mode == "বাংলা (Bengali)":
        body_html = (
            f'<h3 class="cruxly-headline-bn">{h_bn or h_en}</h3>'
            f'<p class="cruxly-body-bn">{brief_bn or brief_en}</p>'
        )
    elif lang_mode == "Bilingual (Side-by-Side)":
        body_html = (
            f'<div class="cruxly-bilingual-grid">'
            f'<div><h3 class="cruxly-headline-en">{h_en}</h3><p class="cruxly-body-en">{brief_en}</p></div>'
            f'<div><h3 class="cruxly-headline-bn">{h_bn or h_en}</h3><p class="cruxly-body-bn">{brief_bn or brief_en}</p></div>'
            f'</div>'
        )
    else:
        body_html = (
            f'<h3 class="cruxly-headline-en">{h_en}</h3>'
            f'<p class="cruxly-body-en">{brief_en}</p>'
        )

    card_html = (
        f'<article class="cruxly-card">'
        f'<div class="cruxly-card-meta">'
        f'<span class="badge-tag">{genre}</span>'
        f'<span class="badge-tag">{geo_label}</span>'
        f'<span class="badge-tag">{slot_label}</span>'
        f'<span class="cruxly-dateline">{dateline}</span>'
        f'</div>'
        f'{body_html}'
        f'{ref_links_html}'
        f'</article>'
    )
    st.markdown(card_html, unsafe_allow_html=True)

    act_col1, act_col2, _ = st.columns([1.3, 1.3, 5.4])
    with act_col1:
        save_label = "★ Saved" if is_saved else "☆ Save"
        if st.button(save_label, key=f"{key_prefix}_save_{sid}"):
            _toggle_save_story(supabase, user_id, sid, is_saved)
            st.rerun()
    with act_col2:
        with st.popover("↗ Share", use_container_width=False):
            primary_link = unique_refs[0]["article_url"] if unique_refs else ""
            share_text = (
                f"{story.get('headline_en') or ''}\n"
                f"{story.get('headline_bn') or ''}\n\n"
                f"{(sum_en_obj.get('in_brief') if isinstance(sum_en_obj, dict) else '')}\n"
                f"{f'Source: {primary_link}' if primary_link else ''}"
            ).strip()
            st.caption("Click the copy icon on the right to copy this briefing:")
            st.code(share_text, language=None)


def render_reader_portal(supabase: Client, user, profile: dict | None = None) -> None:
    """Renders the bilingual editorial Reader Portal with Edition views, Saved News, and full archive pagination."""
    user_id = _extract_user_id(user)
    saved_ids = _fetch_saved_story_ids(supabase, user_id)

    if "reader_feed_limit" not in st.session_state:
        st.session_state.reader_feed_limit = PAGE_SIZE

    # Top Editorial Filter Bar
    f1, f2, f3, f4 = st.columns([1.4, 1.2, 1.5, 1.9])
    with f1:
        lang_mode = st.selectbox(
            "Reading Language",
            ["Bilingual (Side-by-Side)", "English", "বাংলা (Bengali)"],
            key="reader_lang_mode",
        )
    with f2:
        geo_filter = st.selectbox(
            "Geography",
            ["All", "State", "National", "International"],
            key="reader_geo_filter",
        )
    with f3:
        genres = _fetch_active_genres(supabase)
        genre_filter = st.selectbox(
            "Genre",
            ["All"] + genres,
            key="reader_genre_filter",
        )
    with f4:
        search_query = st.text_input(
            "Search Headlines",
            placeholder="Keyword in English or বাংলা...",
            key="reader_search_query",
        )

    tab_all, tab_morning, tab_evening, tab_saved = st.tabs(
        [
            "All / Live Feed",
            "Morning Edition (06:00 AM)",
            "Evening Edition (06:00 PM)",
            f"Saved News ({len(saved_ids)})",
        ]
    )

    with tab_all:
        try:
            stories, total_count = _fetch_stories_page(
                supabase=supabase,
                edition_filter="All",
                geo_filter=geo_filter,
                genre_filter=genre_filter,
                search_query=search_query,
                limit_count=st.session_state.reader_feed_limit,
            )
        except Exception as exc:
            stories, total_count = [], 0
            st.error(f"Could not load stories: {exc}")

        st.caption(f"Showing {len(stories)} of {total_count} consolidated briefings")
        if not stories:
            st.info("No stories match the current filters.")
        else:
            for story in stories:
                _render_story_card(supabase, story, lang_mode, user_id, saved_ids, "all")

            if len(stories) < total_count:
                if st.button(
                    f"Load More Stories ({total_count - len(stories)} remaining)",
                    type="primary",
                    key="load_more_all_btn",
                ):
                    st.session_state.reader_feed_limit += PAGE_SIZE
                    st.rerun()

    with tab_morning:
        try:
            m_stories, m_total = _fetch_stories_page(
                supabase=supabase,
                edition_filter="Morning Edition",
                geo_filter=geo_filter,
                genre_filter=genre_filter,
                search_query=search_query,
                limit_count=st.session_state.reader_feed_limit,
            )
        except Exception as exc:
            m_stories, m_total = [], 0
            st.error(f"Could not load Morning Edition: {exc}")

        st.caption(f"Morning Edition: showing {len(m_stories)} of {m_total} briefings")
        if not m_stories:
            st.info("No stories dispatched specifically under the morning slot for these filters.")
        else:
            for story in m_stories:
                _render_story_card(supabase, story, lang_mode, user_id, saved_ids, "morning")

            if len(m_stories) < m_total:
                if st.button("Load More Morning Stories", key="load_more_morning_btn"):
                    st.session_state.reader_feed_limit += PAGE_SIZE
                    st.rerun()

    with tab_evening:
        try:
            e_stories, e_total = _fetch_stories_page(
                supabase=supabase,
                edition_filter="Evening Edition",
                geo_filter=geo_filter,
                genre_filter=genre_filter,
                search_query=search_query,
                limit_count=st.session_state.reader_feed_limit,
            )
        except Exception as exc:
            e_stories, e_total = [], 0
            st.error(f"Could not load Evening Edition: {exc}")

        st.caption(f"Evening Edition: showing {len(e_stories)} of {e_total} briefings")
        if not e_stories:
            st.info("No stories dispatched specifically under the evening slot for these filters.")
        else:
            for story in e_stories:
                _render_story_card(supabase, story, lang_mode, user_id, saved_ids, "evening")

            if len(e_stories) < e_total:
                if st.button("Load More Evening Stories", key="load_more_evening_btn"):
                    st.session_state.reader_feed_limit += PAGE_SIZE
                    st.rerun()

    with tab_saved:
        saved_stories = _fetch_saved_stories_full(supabase, saved_ids)
        if not saved_stories:
            st.info("You haven't saved any stories yet. Click '☆ Save' on any briefing card to bookmark it here.")
        else:
            for story in saved_stories:
                _render_story_card(supabase, story, lang_mode, user_id, saved_ids, "saved")
