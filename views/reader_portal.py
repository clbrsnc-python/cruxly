from datetime import datetime
import pytz
import streamlit as st
from supabase import Client
from ingestion.processor import APPROVED_GENRES, fetch_approved_genres
from ingestion.sources import get_active_sources

IST = pytz.timezone("Asia/Kolkata")


def _format_story_date(published_at_raw: str | None) -> str:
    """Formats ISO timestamp into date-only '16 Nov 2026' without time."""
    if not published_at_raw:
        return datetime.now(IST).strftime("%d %b %Y")
    try:
        dt = datetime.fromisoformat(published_at_raw.replace("Z", "+00:00"))
        return dt.astimezone(IST).strftime("%d %b %Y")
    except Exception:
        return str(published_at_raw)[:10]


def _pin_to_state(pin_code: str) -> str:
    """Resolves a 6-digit Indian PIN code to its corresponding State/UT."""
    digits = "".join(ch for ch in (pin_code or "") if ch.isdigit())
    if len(digits) < 2:
        return "West Bengal"
    prefix2 = int(digits[:2])
    prefix3 = int(digits[:3]) if len(digits) >= 3 else 0

    if 70 <= prefix2 <= 74:
        return "West Bengal"
    if prefix2 == 11:
        return "Delhi"
    if 12 <= prefix2 <= 13:
        return "Haryana"
    if 14 <= prefix2 <= 16:
        return "Punjab"
    if prefix2 == 17:
        return "Himachal Pradesh"
    if 18 <= prefix2 <= 19:
        return "Jammu & Kashmir / Ladakh"
    if 20 <= prefix2 <= 28:
        return "Uttar Pradesh / Uttarakhand"
    if 30 <= prefix2 <= 34:
        return "Rajasthan"
    if 36 <= prefix2 <= 39:
        return "Gujarat"
    if 40 <= prefix2 <= 44:
        return "Maharashtra / Goa"
    if 45 <= prefix2 <= 49:
        return "Madhya Pradesh / Chhattisgarh"
    if 50 <= prefix2 <= 53:
        return "Telangana / Andhra Pradesh"
    if 56 <= prefix2 <= 59:
        return "Karnataka"
    if 60 <= prefix2 <= 64:
        return "Tamil Nadu / Puducherry"
    if 67 <= prefix2 <= 69:
        return "Kerala"
    if 75 <= prefix2 <= 77:
        return "Odisha"
    if prefix2 == 78:
        return "Assam"
    if prefix3 in (790, 791, 792):
        return "Arunachal Pradesh"
    if prefix3 in (793, 794):
        return "Meghalaya"
    if prefix3 == 795:
        return "Manipur"
    if prefix3 == 796:
        return "Mizoram"
    if prefix3 in (797, 798):
        return "Nagaland"
    if prefix3 == 799:
        return "Tripura"
    if 80 <= prefix2 <= 85:
        return "Bihar / Jharkhand"
    return "West Bengal"


def _get_in_brief_en(summary_en: dict) -> str:
    """Returns unified English 'In brief' text, maintaining backward compatibility."""
    if not summary_en:
        return "—"
    if summary_en.get("in_brief"):
        return str(summary_en["in_brief"]).replace("\n", " ")
    wh = (summary_en.get("what_happened") or "").strip()
    kd = (summary_en.get("key_details") or "").strip()
    combined = f"{wh} {kd}".strip()
    return combined.replace("\n", " ") if combined else "—"


def _get_in_brief_bn(summary_bn: dict) -> str:
    """Returns unified Bengali 'সংক্ষেপে' text, maintaining backward compatibility."""
    if not summary_bn:
        return "—"
    val = summary_bn.get("in_brief") or summary_bn.get("what_happened") or "—"
    return str(val).replace("\n", " ")


def _load_user_preferences(supabase: Client, user_id: str, valid_genres: list[str]) -> dict:
    """Loads persisted reader preferences from public.user_preferences."""
    defaults = {
        "selected_state": "West Bengal",
        "genre_priorities": {g: "Medium" for g in valid_genres},
        "excluded_sources": [],
    }
    try:
        res = (
            supabase.table("user_preferences")
            .select("selected_state, genre_priorities, excluded_sources")
            .eq("user_id", user_id)
            .limit(1)
            .execute()
        )
        if res.data:
            row = res.data[0]
            saved_prios = row.get("genre_priorities") or {}
            merged_prios = {g: saved_prios.get(g, "Medium") for g in valid_genres}
            return {
                "selected_state": row.get("selected_state") or "West Bengal",
                "genre_priorities": merged_prios,
                "excluded_sources": row.get("excluded_sources") or [],
            }
    except Exception:
        pass
    return defaults


def _render_story_cards(
    supabase: Client,
    user,
    stories: list[dict],
    lang_choice: str,
    reader_state: str,
    excluded: set[str],
    key_prefix: str = "feed",
) -> None:
    """Renders bilingual story cards with date below title, unified In brief, and bookmark button."""
    for story in stories:
        s_id = story["id"]
        summary_en = story.get("summary_en") or {}
        summary_bn = story.get("summary_bn") or {}
        refs = story.get("story_references") or []
        date_str = _format_story_date(story.get("published_at"))

        geo_label = story.get("geography", "National")
        story_state = story.get("state_name") or reader_state
        geo_badge = f"State ({story_state})" if geo_label == "State" else geo_label

        headline_en = story.get("headline_en", "Untitled Report")
        headline_bn = story.get("headline_bn") or summary_bn.get("headline_bn") or headline_en

        if lang_choice == "Bengali (বাংলা)":
            title_html = f"<h3>{headline_bn}</h3>"
        elif lang_choice == "Bilingual (English + বাংলা)":
            title_html = f"<h3>{headline_en}<br><span style='font-size: 1.05rem; color: #1B4965;'>{headline_bn}</span></h3>"
        else:
            title_html = f"<h3>{headline_en}</h3>"

        date_html = f'<p style="font-size: 0.9rem; color: #4A6572; margin-top: -0.35rem; margin-bottom: 0.65rem;"><strong>Date:</strong> {date_str}</p>'

        links_html = ""
        if refs:
            anchors = " | ".join(
                f'<a href="{r["article_url"]}" target="_blank" rel="noopener noreferrer">{r["source_name"]}</a>'
                for r in refs
                if r.get("article_url") and r.get("source_name") not in excluded
            )
            if anchors:
                links_html = f'<p style="font-size: 0.95rem; color: #1B4965;"><strong>Original Reporting:</strong> {anchors}</p>'
        elif summary_en.get("sources"):
            links_html = f'<p style="font-size: 0.95rem; color: #1B4965;"><strong>Sources:</strong> {", ".join(summary_en["sources"])}</p>'

        en_html = ""
        if lang_choice in ("English", "Bilingual (English + বাংলা)"):
            en_html = f"<p><strong>In brief:</strong> {_get_in_brief_en(summary_en)}</p>"

        bn_html = ""
        if lang_choice in ("Bengali (বাংলা)", "Bilingual (English + বাংলা)") and summary_bn:
            bn_html = f"<p><strong>সংক্ষেপে:</strong> {_get_in_brief_bn(summary_bn)}</p>"

        card_html = (
            f'<div class="cruxly-card">'
            f'<span class="badge-tag">{story.get("primary_genre", "Politics & Governance")} | {geo_badge}</span>'
            f'{title_html}'
            f'{date_html}'
            f'{en_html}{bn_html}{links_html}'
            f'</div>'
        )
        st.markdown(card_html, unsafe_allow_html=True)

        if st.button("Save Story", key=f"{key_prefix}_bm_{s_id}"):
            try:
                supabase.table("saved_news").upsert(
                    {
                        "user_id": user.id,
                        "story_id": s_id,
                        "saved_at": datetime.now(IST).isoformat(),
                    }
                ).execute()
                st.success("Story saved to Saved News.")
            except Exception as bm_exc:
                st.error(f"Could not save story: {bm_exc}")


def render_reader_portal(supabase: Client, user, profile: dict) -> None:
    """Renders the approved reader workspace: Live Feed, Editions, Archive, Saved News, and Preferences."""
    active_genre_rows = fetch_approved_genres(supabase)
    valid_genres = [g["name_en"] for g in active_genre_rows] or APPROVED_GENRES

    if "prefs_loaded" not in st.session_state:
        persisted = _load_user_preferences(supabase, user.id, valid_genres)
        st.session_state["reader_pin"] = "741235"
        st.session_state["reader_state"] = persisted["selected_state"]
        st.session_state["excluded_sources"] = persisted["excluded_sources"]
        st.session_state["genre_priorities"] = persisted["genre_priorities"]
        st.session_state["prefs_loaded"] = True

    st.markdown(
        '<div class="static-nav">'
        '<span class="nav-pill nav-home">Live Feed</span>'
        '<span class="nav-pill nav-edition">Morning / Evening Editions</span>'
        '<span class="nav-pill nav-archive">3-Month Archive</span>'
        '<span class="nav-pill nav-saved">Saved News</span>'
        '<span class="nav-pill nav-prefs">Preferences</span>'
        '</div>',
        unsafe_allow_html=True,
    )

    tab_feed, tab_editions, tab_archive, tab_saved, tab_prefs = st.tabs(
        [
            "Live Feed",
            "Morning / Evening Editions",
            "3-Month Archive",
            "Saved News",
            "Preferences",
        ]
    )

    # 1. LIVE FEED
    with tab_feed:
        f_col1, f_col2, f_col3 = st.columns([2.2, 1.3, 1.8])
        with f_col1:
            lang_choice = st.radio(
                "Reading Language",
                ["English", "Bengali (বাংলা)", "Bilingual (English + বাংলা)"],
                horizontal=True,
                key="feed_lang",
            )
        with f_col2:
            geo_filter = st.selectbox(
                f"Geography (State: {st.session_state['reader_state']})",
                ["All", "State", "National", "International"],
                key="feed_geo_filter",
            )
        with f_col3:
            genre_filter = st.selectbox(
                "Subject / Genre (Approved DPR Categories)",
                ["All Genres"] + valid_genres,
                key="feed_genre_filter",
            )

        try:
            query = (
                supabase.table("stories")
                .select("*, story_references(source_name, article_url, hindi_original_headline)")
                .eq("status", "published")
            )
            if geo_filter != "All":
                query = query.eq("geography", geo_filter)
            if genre_filter != "All Genres":
                query = query.eq("primary_genre", genre_filter)

            stories_res = query.order("published_at", desc=True).limit(30).execute()
            stories = stories_res.data or []
        except Exception as exc:
            stories = []
            st.error(f"Could not load published stories: {exc}")

        excluded = set(st.session_state.get("excluded_sources") or [])
        if excluded and stories:
            filtered_stories = []
            for s in stories:
                refs = s.get("story_references") or []
                ref_names = {r.get("source_name") for r in refs if r.get("source_name")}
                if not ref_names or not ref_names.issubset(excluded):
                    filtered_stories.append(s)
            if filtered_stories:
                stories = filtered_stories

        priority_rank = {"High": 0, "Medium": 1, "Low": 2}
        g_prios = st.session_state.get("genre_priorities") or {}
        stories.sort(
            key=lambda s: (
                priority_rank.get(g_prios.get(s.get("primary_genre"), "Medium"), 1),
            )
        )

        if not stories:
            st.markdown(
                '<div class="cruxly-card">'
                '<h3>No Stories Match Current Filter</h3>'
                '<p>Switch Geography back to <strong>All</strong> or Subject / Genre back to <strong>All Genres</strong> to view all published briefings.</p>'
                '</div>',
                unsafe_allow_html=True,
            )
        else:
            _render_story_cards(
                supabase=supabase,
                user=user,
                stories=stories,
                lang_choice=lang_choice,
                reader_state=st.session_state["reader_state"],
                excluded=excluded,
                key_prefix="live",
            )

    # 2. MORNING / EVENING EDITIONS
    with tab_editions:
        ed_col1, ed_col2 = st.columns([1.8, 2.2])
        with ed_col1:
            edition_choice = st.radio(
                "Select Consolidated Edition",
                ["Morning Edition (06:00 AM IST)", "Evening Edition (06:00 PM IST)"],
                horizontal=True,
                key="edition_slot_radio",
            )
        with ed_col2:
            ed_lang = st.radio(
                "Edition Language",
                ["English", "Bengali (বাংলা)", "Bilingual (English + বাংলা)"],
                horizontal=True,
                key="edition_lang_radio",
            )

        slot_key = "morning" if "Morning" in edition_choice else "evening"
        try:
            ed_res = (
                supabase.table("stories")
                .select("*, story_references(source_name, article_url, hindi_original_headline)")
                .eq("status", "published")
                .eq("edition_slot", slot_key)
                .order("published_at", desc=True)
                .limit(20)
                .execute()
            )
            ed_stories = ed_res.data or []
        except Exception as ed_exc:
            ed_stories = []
            st.error(f"Could not load {slot_key} edition: {ed_exc}")

        if not ed_stories:
            st.markdown(
                f'<div class="cruxly-card">'
                f'<h3>{edition_choice} — Awaiting Next Scheduled Dispatch</h3>'
                f'<p>No stories have been dispatched specifically under the <strong>{slot_key}</strong> slot yet. '
                f'Administrators can trigger a {slot_key} edition cycle from the Administrator Console, or view all latest stories in the Live Feed.</p>'
                f'</div>',
                unsafe_allow_html=True,
            )
        else:
            _render_story_cards(
                supabase=supabase,
                user=user,
                stories=ed_stories,
                lang_choice=ed_lang,
                reader_state=st.session_state["reader_state"],
                excluded=set(st.session_state.get("excluded_sources") or []),
                key_prefix=f"ed_{slot_key}",
            )

    # 3. 3-MONTH ARCHIVE
    with tab_archive:
        search_q = st.text_input("Search 3-month verified archive by keyword, topic, or location", key="archive_search")
        if search_q:
            try:
                arch_res = (
                    supabase.table("stories")
                    .select("id, headline_en, headline_bn, primary_genre, geography, published_at")
                    .eq("status", "published")
                    .ilike("headline_en", f"%{search_q}%")
                    .order("published_at", desc=True)
                    .limit(25)
                    .execute()
                )
                results = arch_res.data or []
                if not results:
                    st.info("No archived reports matched your search term.")
                for row in results:
                    r_date = _format_story_date(row.get("published_at"))
                    arch_card_html = (
                        f'<div class="cruxly-card">'
                        f'<span class="badge-tag">{row.get("primary_genre", "News")} | {row.get("geography", "National")}</span>'
                        f'<h3>{row.get("headline_en", "Untitled")}</h3>'
                        f'<p style="font-size: 0.9rem; color: #4A6572; margin-top: -0.35rem;"><strong>Date:</strong> {r_date}</p>'
                        f'</div>'
                    )
                    st.markdown(arch_card_html, unsafe_allow_html=True)
            except Exception as arch_exc:
                st.error(f"Archive search error: {arch_exc}")

    # 4. SAVED NEWS (WIRED TO public.saved_news)
    with tab_saved:
        try:
            saved_res = (
                supabase.table("saved_news")
                .select("story_id, saved_at, stories(id, headline_en, headline_bn, primary_genre, geography, published_at)")
                .eq("user_id", user.id)
                .order("saved_at", desc=True)
                .execute()
            )
            saved_items = saved_res.data or []
        except Exception:
            saved_items = []

        if not saved_items:
            st.info("You have not saved any stories yet.")
        else:
            for item in saved_items:
                st_info = item.get("stories") or {}
                s_date = _format_story_date(st_info.get("published_at"))
                saved_card_html = (
                    f'<div class="cruxly-card">'
                    f'<span class="badge-tag">{st_info.get("primary_genre", "Saved")} | {st_info.get("geography", "National")}</span>'
                    f'<h3>{st_info.get("headline_en", "Saved Report")}</h3>'
                    f'<p style="font-size: 0.9rem; color: #4A6572; margin-top: -0.35rem;"><strong>Date:</strong> {s_date}</p>'
                    f'</div>'
                )
                st.markdown(saved_card_html, unsafe_allow_html=True)

    # 5. PREFERENCES (PERSISTED TO public.user_preferences)
    with tab_prefs:
        prefs_card_html = (
            f'<div class="cruxly-card">'
            f'<h3>Reader Profile &amp; DPR Feed Preferences</h3>'
            f'<p><strong>Name:</strong> {profile.get("full_name") or "Registered Reader"} | '
            f'<strong>Email:</strong> {profile.get("email")} | '
            f'<strong>Status:</strong> {profile.get("account_status", "approved").upper()}</p>'
            f'</div>'
        )
        st.markdown(prefs_card_html, unsafe_allow_html=True)

        st.markdown("#### State Location via PIN Code")
        p_col1, p_col2 = st.columns([1.5, 2.5])
        with p_col1:
            pin_val = st.text_input(
                "6-Digit Indian PIN Code",
                value=st.session_state["reader_pin"],
                max_chars=6,
                key="pin_input",
            )
            if pin_val != st.session_state["reader_pin"]:
                st.session_state["reader_pin"] = pin_val
                st.session_state["reader_state"] = _pin_to_state(pin_val)
        with p_col2:
            indian_states = [
                "West Bengal", "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar / Jharkhand",
                "Delhi", "Gujarat", "Haryana", "Himachal Pradesh", "Jammu & Kashmir / Ladakh",
                "Karnataka", "Kerala", "Madhya Pradesh / Chhattisgarh", "Maharashtra / Goa",
                "Manipur", "Meghalaya", "Mizoram", "Nagaland", "Odisha", "Punjab",
                "Rajasthan", "Tamil Nadu / Puducherry", "Telangana / Andhra Pradesh",
                "Tripura", "Uttar Pradesh / Uttarakhand",
            ]
            current_state = st.session_state["reader_state"]
            idx = indian_states.index(current_state) if current_state in indian_states else 0
            manual_state = st.selectbox(
                "Active State for 'State' Geography Stories (Auto-detected from PIN or override manually)",
                indian_states,
                index=idx,
                key="manual_state_select",
            )
            st.session_state["reader_state"] = manual_state

        st.markdown("#### Newspaper Source Exclusions")
        all_source_names = sorted({src["name"] for src in get_active_sources()})
        excluded_sel = st.multiselect(
            "Exclude specific newspapers (National & International stories remain visible; feed never empties)",
            all_source_names,
            default=st.session_state["excluded_sources"],
            key="exclude_sources_multiselect",
        )
        st.session_state["excluded_sources"] = excluded_sel

        st.markdown("#### Approved DPR Genres — Feed Priority")
        g_cols = st.columns(3)
        for i, genre_name in enumerate(valid_genres):
            with g_cols[i % 3]:
                prio = st.selectbox(
                    genre_name,
                    ["High", "Medium", "Low"],
                    index=["High", "Medium", "Low"].index(
                        st.session_state["genre_priorities"].get(genre_name, "Medium")
                    ),
                    key=f"prio_{genre_name}",
                )
                st.session_state["genre_priorities"][genre_name] = prio

        if st.button("Save Preferences to Profile", type="primary", key="save_prefs_btn"):
            try:
                supabase.table("user_preferences").upsert(
                    {
                        "user_id": user.id,
                        "selected_state": st.session_state["reader_state"],
                        "genre_priorities": st.session_state["genre_priorities"],
                        "excluded_sources": st.session_state["excluded_sources"],
                        "updated_at": datetime.now(IST).isoformat(),
                    }
                ).execute()
                st.success("Your State, Genre Priority, and Newspaper Exclusion preferences have been saved.")
            except Exception as pref_exc:
                st.error(f"Could not save preferences: {pref_exc}")
