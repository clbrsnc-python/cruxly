import streamlit as st
from supabase import Client
from ingestion.processor import run_ingestion_cycle


def render_admin_portal(supabase: Client, current_user_id: str, user_roles: list[str]) -> None:
    """Renders the Administrator Console for Reader Access Governance, News Ingestion, and Audit Logs."""
    is_super_admin = "super_admin" in user_roles

    st.markdown("---")
    st.markdown("### Administrator Console — Governance & News Pipeline")

    tab_users, tab_ingest, tab_audit = st.tabs(
        ["User Approval & Governance", "News Ingestion Control", "System Audit Logs"]
    )

    # 1. USER APPROVAL & GOVERNANCE
    with tab_users:
        status_filter = st.selectbox(
            "Filter Accounts by Status",
            ["All", "pending", "approved", "rejected"],
            key="admin_user_filter",
        )
        try:
            query = supabase.table("users").select(
                "id, full_name, email, account_status, roles, approved_by, approved_at, rejection_reason"
            )
            if status_filter != "All":
                query = query.eq("account_status", status_filter)
            all_users_res = query.order("email").execute()
            all_users = all_users_res.data or []
        except Exception as admin_exc:
            all_users = []
            st.error(f"Could not load user directory: {admin_exc}")

        if not all_users:
            st.info("No user records match the selected filter.")

        for u_row in all_users:
            u_id = u_row["id"]
            u_status = u_row.get("account_status", "pending")
            u_roles = ", ".join(u_row.get("roles") or ["app_user"])
            rej_note = u_row.get("rejection_reason")

            user_card_html = (
                f'<div class="cruxly-card">'
                f'<span class="badge-tag">Status: {u_status.upper()} | Roles: {u_roles}</span>'
                f'<h3>{u_row.get("full_name") or "Reader"} ({u_row.get("email")})</h3>'
                f'<p style="font-size: 0.92rem; color: #1B4965;">'
                f'Reviewed At: {u_row.get("approved_at") or "—"} | '
                f'Reviewed By ID: {u_row.get("approved_by") or "—"}'
                f'{f" | Reason: {rej_note}" if rej_note else ""}'
                f'</p>'
                f'</div>'
            )
            st.markdown(user_card_html, unsafe_allow_html=True)

            if u_id != current_user_id:
                c1, c2, c3 = st.columns([1, 1, 3])
                with c3:
                    reason_input = st.text_input(
                        "Optional rejection note",
                        key=f"reason_{u_id}",
                        placeholder="Enter reason if rejecting...",
                        label_visibility="collapsed",
                    )
                with c1:
                    if u_status != "approved" and st.button("Approve", key=f"app_{u_id}"):
                        supabase.table("users").update(
                            {"account_status": "approved", "rejection_reason": None}
                        ).eq("id", u_id).execute()
                        st.rerun()
                with c2:
                    if u_status != "rejected" and st.button("Reject", key=f"rej_{u_id}"):
                        supabase.table("users").update(
                            {
                                "account_status": "rejected",
                                "rejection_reason": reason_input.strip() or None,
                            }
                        ).eq("id", u_id).execute()
                        st.rerun()

    # 2. MANUAL NEWS INGESTION TEST TRIGGER (Super Admin Only)
    with tab_ingest:
        if not is_super_admin:
            st.info("News ingestion controls are restricted to Super Administrators.")
        else:
            gemini_key = st.secrets.get("GEMINI_API_KEY")
            groq_key = st.secrets.get("GROQ_API_KEY")
            ai_status = (
                "Groq API Connected"
                if groq_key
                else (
                    "Gemini API Connected"
                    if gemini_key
                    else "Fallback Mode (Add GROQ_API_KEY or GEMINI_API_KEY in Streamlit Secrets for AI bilingual synthesis)"
                )
            )
            ingest_card_html = (
                f'<div class="cruxly-card">'
                f'<h3>Multi-Source RSS Collection &amp; Cross-Verification</h3>'
                f'<p><strong>Synthesis Engine:</strong> {ai_status}</p>'
                f'<p>Click below to collect current headlines across your selected English, Bengali, and Hindi sources, cluster matching reports, and publish consolidated briefings to the Live Feed.</p>'
                f'</div>'
            )
            st.markdown(ingest_card_html, unsafe_allow_html=True)

            if st.button("Run News Cycle Now", key="run_news_cycle_btn"):
                with st.spinner("Collecting RSS feeds, clustering stories, and publishing consolidated briefings..."):
                    result = run_ingestion_cycle(
                        supabase,
                        gemini_api_key=gemini_key,
                        groq_api_key=groq_key,
                    )
                st.session_state["last_ingest_result"] = result

            if "last_ingest_result" in st.session_state:
                res = st.session_state["last_ingest_result"]
                if res.get("published", 0) > 0:
                    st.success(res["message"])
                else:
                    st.warning(res.get("message", "No new stories were published."))

    # 3. IMMUTABLE AUDIT LOGS (Super Admin Only)
    with tab_audit:
        if not is_super_admin:
            st.info("Audit logs are restricted to Super Administrators.")
        else:
            try:
                logs_res = (
                    supabase.table("audit_logs")
                    .select("created_at, action_type, target_entity, actor_id, outcome, before_state, after_state")
                    .order("created_at", desc=True)
                    .limit(30)
                    .execute()
                )
                logs = logs_res.data or []
            except Exception as log_exc:
                logs = []
                st.error(f"Could not load audit logs: {log_exc}")

            if not logs:
                st.info("No governance audit events recorded yet.")
            else:
                for log in logs:
                    log_card_html = (
                        f'<div class="cruxly-card">'
                        f'<span class="badge-tag">{log.get("action_type", "event")} | Outcome: {log.get("outcome", "success")}</span>'
                        f'<p><strong>Timestamp:</strong> {log.get("created_at")} | <strong>Target:</strong> {log.get("target_entity")}</p>'
                        f'<p style="font-size: 0.9rem; color: #1B4965;">'
                        f'<strong>Before:</strong> {log.get("before_state")} → <strong>After:</strong> {log.get("after_state")}'
                        f'</p>'
                        f'</div>'
                    )
                    st.markdown(log_card_html, unsafe_allow_html=True)
