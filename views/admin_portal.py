import streamlit as st
from supabase import Client


def render_admin_portal(supabase: Client, current_user_id: str, user_roles: list[str]) -> None:
    """Renders the Administrator Console for Reader Access Governance and Audit Logs."""
    is_super_admin = "super_admin" in user_roles

    st.markdown("---")
    st.markdown("### Administrator Console — Reader Access Governance")

    tab_users, tab_audit = st.tabs(["User Approval & Governance", "System Audit Logs"])

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

            st.markdown(
                f"""
                <div class="cruxly-card">
                    <span class="badge-tag">Status: {u_status.upper()} | Roles: {u_roles}</span>
                    <h3>{u_row.get('full_name') or 'Reader'} ({u_row.get('email')})</h3>
                    <p style="font-size: 0.92rem; color: #1B4965;">
                        Reviewed At: {u_row.get('approved_at') or '—'} |
                        Reviewed By ID: {u_row.get('approved_by') or '—'}
                        {f' | Reason: {rej_note}' if rej_note else ''}
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )

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

    # 2. IMMUTABLE AUDIT LOGS (Super Admin Only)
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
                    st.markdown(
                        f"""
                        <div class="cruxly-card">
                            <span class="badge-tag">{log.get('action_type', 'event')} | Outcome: {log.get('outcome', 'success')}</span>
                            <p><strong>Timestamp:</strong> {log.get('created_at')} | <strong>Target:</strong> {log.get('target_entity')}</p>
                            <p style="font-size: 0.9rem; color: #1B4965;">
                                <strong>Before:</strong> {log.get('before_state')} → <strong>After:</strong> {log.get('after_state')}
                            </p>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
