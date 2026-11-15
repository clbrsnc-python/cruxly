import streamlit as st
from supabase import Client


def render_reader_portal(supabase: Client, user, profile: dict) -> None:
    """Renders the approved reader workspace: Live Feed, Editions, Archive, Saved News, and Preferences."""
    st.markdown(
        """
        <div class="static-nav">
            <span class="nav-pill nav-home">Live Feed</span>
            <span class="nav-pill nav-edition">Morning / Evening Editions</span>
            <span class="nav-pill nav-archive">3-Month Archive</span>
            <span class="nav-pill nav-saved">Saved News</span>
            <span class="nav-pill nav-prefs">Preferences</span>
        </div>
        """,
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
        lang_choice = st.radio(
            "Reading Language",
            ["English", "Bengali (বাংলা)", "Bilingual (English + বাংলা)"],
            horizontal=True,
            key="feed_lang",
        )
        try:
            stories_res = (
                supabase.table("stories")
                .select("*, story_references(publisher_name, article_url, language)")
                .eq("status", "published")
                .order("published_at", desc=True)
                .limit(20)
                .execute()
            )
            stories = stories_res.data or []
        except Exception as exc:
            stories = []
            st.error(f"Could not load published stories: {exc}")

        if not stories:
            st.markdown(
                """
                <div class="cruxly-card">
                    <h3>Cruxly Foundation Connected — Ready for First News Cycle</h3>
                    <p>Your reader portal is active. Consolidated multi-source news stories will appear here automatically once the RSS ingestion pipeline publishes its first verified cycle.</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            for story in stories:
                s_id = story["id"]
                summary_en = story.get("summary_en") or {}
                summary_bn = story.get("summary_bn") or {}
                refs = story.get("story_references") or []

                links_html = ""
                if refs:
                    anchors = " | ".join(
                        f'<a href="{r["article_url"]}" target="_blank" rel="noopener noreferrer">{r["publisher_name"]}</a>'
                        for r in refs
                        if r.get("article_url")
                    )
                    if anchors:
                        links_html = f'<p style="font-size: 0.95rem; color: #1B4965;"><strong>Original Reporting:</strong> {anchors}</p>'

                en_html = ""
                if lang_choice in ("English", "Bilingual (English + বাংলা)"):
                    en_html = (
                        f"<p><strong>What Happened:</strong> {summary_en.get('what_happened', '—')}</p>"
                        f"<p><strong>Key Details:</strong> {summary_en.get('key_details', '—')}</p>"
                    )

                bn_html = ""
                if lang_choice in ("Bengali (বাংলা)", "Bilingual (English + বাংলা)") and summary_bn:
                    bn_html = f"<p><strong>সারসংক্ষেপ:</strong> {summary_bn.get('what_happened', '—')}</p>"

                st.markdown(
                    f"""
                    <div class="cruxly-card">
                        <span class="badge-tag">{story.get('primary_genre', 'General')} | {story.get('geography', 'National')}</span>
                        <h3>{story.get('headline_en', 'Untitled Report')}</h3>
                        {en_html}
                        {bn_html}
                        {links_html}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                if st.button("Bookmark Story", key=f"bm_{s_id}"):
                    try:
                        supabase.table("bookmarks").upsert(
                            {"user_id": user.id, "story_id": s_id}
                        ).execute()
                        st.success("Story saved to your bookmarks.")
                    except Exception as bm_exc:
                        st.error(f"Could not bookmark story: {bm_exc}")

    # 2. MORNING / EVENING EDITIONS
    with tab_editions:
        st.markdown(
            """
            <div class="cruxly-card">
                <h3>Scheduled Consolidated Editions</h3>
                <p>Curated morning and evening briefings summarizing major verified developments across National, State, International, Economy, and Science &amp; Technology desks.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # 3. 3-MONTH ARCHIVE
    with tab_archive:
        search_q = st.text_input("Search 3-month verified archive by keyword, topic, or location", key="archive_search")
        if search_q:
            try:
                arch_res = (
                    supabase.table("stories")
                    .select("id, headline_en, primary_genre, geography, published_at")
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
                    st.markdown(
                        f"""
                        <div class="cruxly-card">
                            <span class="badge-tag">{row.get('primary_genre', 'News')} | {row.get('geography', 'National')}</span>
                            <h3>{row.get('headline_en', 'Untitled')}</h3>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
            except Exception as arch_exc:
                st.error(f"Archive search error: {arch_exc}")

    # 4. SAVED NEWS
    with tab_saved:
        try:
            saved_res = (
                supabase.table("bookmarks")
                .select("story_id, created_at, stories(id, headline_en, primary_genre, geography)")
                .eq("user_id", user.id)
                .order("created_at", desc=True)
                .execute()
            )
            saved_items = saved_res.data or []
        except Exception:
            saved_items = []

        if not saved_items:
            st.info("You have not bookmarked any stories yet.")
        else:
            for item in saved_items:
                st_info = item.get("stories") or {}
                st.markdown(
                    f"""
                    <div class="cruxly-card">
                        <span class="badge-tag">{st_info.get('primary_genre', 'Saved')} | {st_info.get('geography', 'National')}</span>
                        <h3>{st_info.get('headline_en', 'Saved Report')}</h3>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    # 5. PREFERENCES
    with tab_prefs:
        st.markdown(
            f"""
            <div class="cruxly-card">
                <h3>Reader Profile &amp; Feed Preferences</h3>
                <p><strong>Name:</strong> {profile.get('full_name') or 'Registered Reader'}</p>
                <p><strong>Email:</strong> {profile.get('email')}</p>
                <p><strong>Account Status:</strong> {profile.get('account_status', 'approved').upper()}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
