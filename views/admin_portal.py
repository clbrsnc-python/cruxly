from datetime import datetime
import pytz
import streamlit as st
from supabase import Client
from ingestion.processor import (
    DEFAULT_DPR_GENRES,
    run_ingestion_cycle,
)
from ingestion.sources import get_active_sources

IST = pytz.timezone("Asia/Kolkata")


def _extract_actor_id(user_obj) -> str:
    """Safely extracts UUID string whether app.py passes user.id (str) or a Supabase User object."""
    if isinstance(user_obj, str):
        return user_obj
    return str(getattr(user_obj, "id", "") or "")


def _log_admin_action(
    supabase: Client,
    actor_id: str,
    action_type: str,
    action: str,
    target_table: str,
    target_entity: str,
    target_id: str | None = None,
    before_state: dict | None = None,
    after_state: dict | None = None,
) -> None:
    """Records immutable administrative governance actions in public.audit_logs."""
    try:
        payload = {
            "actor_id": actor_id,
            "action_type": action_type,
            "action": action,
            "target_table": target_table,
            "target_entity": target_entity,
            "target_id": target_id,
            "before_state": before_state or {},
            "after_state": after_state or {},
            "outcome": "success",
            "created_at": datetime.now(IST).isoformat(),
        }
        supabase.table("audit_logs").insert(payload).execute()
    except Exception:
        pass


def render_admin_portal(supabase: Client, user, profile: dict) -> None:
    """Renders the Super Admin / Admin governance console per DPR specifications."""
    actor_id = _extract_actor_id(user)

    st.markdown(
        '<div class="cruxly-card">'
        '<h3>Administrator Governance Console</h3>'
        '<p>Manage reader onboarding approvals, run Live / Morning / Evening / Exhaustive Backfill synthesis cycles, '
        'govern the 12 approved DPR genres, and moderate sensitive stories with full audit logging.</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    tab_users, tab_ingest, tab_genres, tab_stories, tab_audit = st.tabs(
        [
            "User Approvals",
            "News Ingestion Control",
            "Genre Governance (DPR)",
            "Story & Sensitive Review",
            "Audit Logs",
        ]
    )

    # 1. USER APPROVALS
    with tab_users:
        try:
            users_res = (
                supabase.table("users")
                .select("id, full_name, email, role, account_status, created_at")
                .order("created_at", desc=True)
                .execute()
            )
            all_users = users_res.data or []
        except Exception as exc:
            all_users = []
            st.error(f"Could not fetch user accounts: {exc}")

        pending = [u for u in all_users if u.get("account_status") == "pending"]
        st.markdown(f"#### Pending Registration Requests ({len(pending)})")
        if not pending:
            st.info("No pending reader accounts awaiting approval.")
        else:
            for u in pending:
                uid = u["id"]
                st.markdown(
                    f'<div class="cruxly-card">'
                    f'<h3>{u.get("full_name") or "Applicant"}</h3>'
                    f'<p><strong>Email:</strong> {u.get("email")} | <strong>Role:</strong> {u.get("role")}</p>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("Approve Reader", key=f"app_{uid}"):
                        supabase.table("users").update({"account_status": "approved"}).eq("id", uid).execute()
                        _log_admin_action(
                            supabase,
                            actor_id,
                            "USER_APPROVAL",
                            "Approved reader account",
                            "users",
                            u.get("email", uid),
                            target_id=uid,
                            before_state={"account_status": "pending"},
                            after_state={"account_status": "approved"},
                        )
                        st.success(f"Approved {u.get('email')}.")
                        st.rerun()
                with c2:
                    if st.button("Reject Application", key=f"rej_{uid}"):
                        supabase.table("users").update({"account_status": "rejected"}).eq("id", uid).execute()
                        _log_admin_action(
                            supabase,
                            actor_id,
                            "USER_REJECTION",
                            "Rejected reader account",
                            "users",
                            u.get("email", uid),
                            target_id=uid,
                            before_state={"account_status": "pending"},
                            after_state={"account_status": "rejected"},
                        )
                        st.warning(f"Rejected {u.get('email')}.")
                        st.rerun()

    # 2. NEWS INGESTION CONTROL (LIVE, MORNING, EVENING, EXHAUSTIVE BACKFILL)
    with tab_ingest:
        sources = get_active_sources()
        st.markdown(
            f'<div class="cruxly-card">'
            f'<h3>Active RSS Collection Registry ({len(sources)} Newspapers)</h3>'
            f'<p>Collects headlines and snippets across English, Bengali, and Hindi dailies, '
            f'automatically excludes astrology/horoscope clutter, clusters related reports across languages, '
            f'runs 2-pass Bengali copy-editing, and publishes consolidated bilingual briefings.</p>'
            f'</div>',
            unsafe_allow_html=True,
        )

        ic1, ic2 = st.columns([2, 1.5])
        with ic1:
            slot_choice = st.selectbox(
                "Target Edition Slot",
                ["live", "morning", "evening"],
                format_func=lambda s: {
                    "live": "Live Feed (Instant Update)",
                    "morning": "Morning Consolidated Edition (06:00 AM IST Slot)",
                    "evening": "Evening Consolidated Edition (06:00 PM IST Slot)",
                }[s],
                key="admin_edition_slot",
            )
        with ic2:
            exhaustive_on = st.checkbox(
                "Exhaustive Backfill Mode (All unique clusters from date)",
                value=False,
                key="admin_exhaustive_toggle",
            )

        since_str = None
        if exhaustive_on:
            since_val = st.date_input(
                "Collect All Non-Astrology Stories From Date",
                value=datetime(2026, 11, 15).date(),
                key="admin_since_date",
            )
            since_str = since_val.strftime("%Y-%m-%d")

        if st.button("Run News Cycle Now", type="primary", key="run_cycle_btn"):
            gemini_key = st.secrets.get("GEMINI_API_KEY")
            groq_key = st.secrets.get("GROQ_API_KEY")
            with st.spinner("Fetching feeds, filtering astrology, clustering reports, and synthesizing bilingual briefings..."):
                result = run_ingestion_cycle(
                    supabase,
                    gemini_api_key=gemini_key,
                    groq_api_key=groq_key,
                    edition_slot=slot_choice,
                    since_date=since_str,
                    exhaustive=exhaustive_on,
                )
            _log_admin_action(
                supabase,
                actor_id,
                "INGESTION_RUN",
                f"Executed {slot_choice} ingestion cycle (exhaustive={exhaustive_on})",
                "stories",
                f"edition:{slot_choice}",
                after_state=result,
            )
            st.success(result["message"])

    # 3. GENRE GOVERNANCE (DPR SECTION: ADD / EDIT / DELETE WITH STORY REASSIGNMENT)
    with tab_genres:
        st.markdown(
            '<div class="cruxly-card">'
            '<h3>Approved DPR Genres Management</h3>'
            '<p>AI classifies stories strictly within currently active genres below. '
            'Deleting or deactivating a genre requires reassigning existing stories to another active genre first.</p>'
            '</div>',
            unsafe_allow_html=True,
        )

        try:
            g_res = supabase.table("genres").select("*").order("id").execute()
            db_genres = g_res.data or []
        except Exception as g_exc:
            db_genres = []
            st.error(f"Could not load public.genres: {g_exc}")

        if not db_genres:
            st.warning("public.genres table is currently empty. Seed the 12 official DPR genres in one click:")
            if st.button("Seed 12 Official DPR Genres", type="primary", key="seed_genres_btn"):
                seed_rows = [
                    {"name_en": g["name_en"], "name_bn": g["name_bn"], "is_active": True}
                    for g in DEFAULT_DPR_GENRES
                ]
                supabase.table("genres").insert(seed_rows).execute()
                _log_admin_action(
                    supabase,
                    actor_id,
                    "GENRE_SEED",
                    "Seeded 12 official DPR genres",
                    "genres",
                    "default_12_genres",
                )
                st.success("Seeded all 12 approved DPR genres.")
                st.rerun()

        with st.expander("Add New Approved Genre"):
            new_en = st.text_input("Genre Name (English)", key="new_genre_en")
            new_bn = st.text_input("Genre Name (Bengali / বাংলা)", key="new_genre_bn")
            if st.button("Create Genre", key="create_genre_btn"):
                if new_en.strip() and new_bn.strip():
                    supabase.table("genres").insert(
                        {"name_en": new_en.strip(), "name_bn": new_bn.strip(), "is_active": True}
                    ).execute()
                    _log_admin_action(
                        supabase,
                        actor_id,
                        "GENRE_CREATE",
                        f"Added genre {new_en.strip()}",
                        "genres",
                        new_en.strip(),
                        after_state={"name_en": new_en.strip(), "name_bn": new_bn.strip()},
                    )
                    st.success(f"Added '{new_en.strip()}'.")
                    st.rerun()
                else:
                    st.warning("Please enter both English and Bengali genre names.")

        if db_genres:
            active_names = [g["name_en"] for g in db_genres if g.get("is_active", True)]
            for g_row in db_genres:
                gid = g_row["id"]
                g_en = g_row["name_en"]
                g_bn = g_row.get("name_bn") or ""
                is_act = g_row.get("is_active", True)

                col1, col2, col3 = st.columns([2.2, 1.8, 1.5])
                with col1:
                    st.markdown(f"**{g_en}** ({g_bn}) — `{'ACTIVE' if is_act else 'INACTIVE'}`")
                with col2:
                    other_targets = [name for name in active_names if name != g_en]
                    target_genre = st.selectbox(
                        "Reassign stories to",
                        other_targets or ["Politics & Governance"],
                        key=f"reassign_target_{gid}",
                        label_visibility="collapsed",
                    )
                with col3:
                    if st.button("Reassign & Delete", key=f"del_genre_{gid}"):
                        supabase.table("stories").update({"primary_genre": target_genre}).eq("primary_genre", g_en).execute()
                        supabase.table("genres").delete().eq("id", gid).execute()
                        _log_admin_action(
                            supabase,
                            actor_id,
                            "GENRE_DELETE",
                            f"Reassigned '{g_en}' to '{target_genre}' and deleted genre",
                            "genres",
                            g_en,
                            before_state={"deleted_genre": g_en},
                            after_state={"reassigned_to": target_genre},
                        )
                        st.success(f"Reassigned stories to '{target_genre}' and deleted '{g_en}'.")
                        st.rerun()

    # 4. STORY & SENSITIVE NEWS MODERATION
    with tab_stories:
        st.markdown("#### Recent Stories & Sensitive News Safeguard Queue")
        status_filter = st.selectbox(
            "Filter by Publication Status",
            ["All", "flagged_review", "published", "withheld_sensitive"],
            key="admin_story_status_filter",
        )
        try:
            sq = supabase.table("stories").select(
                "id, headline_en, headline_bn, primary_genre, geography, edition_slot, status, published_at"
            )
            if status_filter != "All":
                sq = sq.eq("status", status_filter)
            s_res = sq.order("published_at", desc=True).limit(25).execute()
            recent_stories = s_res.data or []
        except Exception as s_exc:
            recent_stories = []
            st.error(f"Could not fetch stories: {s_exc}")

        if not recent_stories:
            st.info("No stories found for the selected status.")
        else:
            for st_row in recent_stories:
                sid = st_row["id"]
                cur_status = st_row.get("status", "published")
                st.markdown(
                    f'<div class="cruxly-card">'
                    f'<span class="badge-tag">{st_row.get("primary_genre")} | {st_row.get("geography")} | {st_row.get("edition_slot", "live").upper()} | {cur_status.upper()}</span>'
                    f'<h3>{st_row.get("headline_en")}</h3>'
                    f'<p>{st_row.get("headline_bn") or ""}</p>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
                sc1, sc2, sc3 = st.columns(3)
                with sc1:
                    if cur_status != "published" and st.button("Approve & Publish", key=f"pub_{sid}"):
                        supabase.table("stories").update({"status": "published"}).eq("id", sid).execute()
                        _log_admin_action(
                            supabase,
                            actor_id,
                            "STORY_PUBLISH",
                            "Published story",
                            "stories",
                            st_row.get("headline_en", sid)[:80],
                            target_id=sid,
                            before_state={"status": cur_status},
                            after_state={"status": "published"},
                        )
                        st.rerun()
                with sc2:
                    if cur_status != "flagged_review" and st.button("Flag for Review", key=f"flg_{sid}"):
                        supabase.table("stories").update({"status": "flagged_review"}).eq("id", sid).execute()
                        _log_admin_action(
                            supabase,
                            actor_id,
                            "STORY_FLAG",
                            "Flagged story for review",
                            "stories",
                            st_row.get("headline_en", sid)[:80],
                            target_id=sid,
                            before_state={"status": cur_status},
                            after_state={"status": "flagged_review"},
                        )
                        st.rerun()
                with sc3:
                    if cur_status != "withheld_sensitive" and st.button("Withhold (Sensitive)", key=f"wh_{sid}"):
                        supabase.table("stories").update({"status": "withheld_sensitive"}).eq("id", sid).execute()
                        _log_admin_action(
                            supabase,
                            actor_id,
                            "STORY_WITHHOLD",
                            "Withheld sensitive story",
                            "stories",
                            st_row.get("headline_en", sid)[:80],
                            target_id=sid,
                            before_state={"status": cur_status},
                            after_state={"status": "withheld_sensitive"},
                        )
                        st.rerun()

    # 5. AUDIT LOGS
    with tab_audit:
        st.markdown("#### Governance & Editorial Audit Trail")
        try:
            logs_res = (
                supabase.table("audit_logs")
                .select("created_at, action_type, action, target_entity, outcome")
                .order("created_at", desc=True)
                .limit(30)
                .execute()
            )
            logs = logs_res.data or []
            if not logs:
                st.info("No audit log entries recorded yet.")
            else:
                st.dataframe(logs, use_container_width=True)
        except Exception as log_exc:
            st.error(f"Could not fetch audit logs: {log_exc}")
