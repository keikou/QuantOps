from __future__ import annotations

from ai_hedge_bot.governance_audit.models import AuditEvidenceBundle


class AuditBundleBuilder:
    def __init__(self, store) -> None:
        self.store = store

    def build_for_incident(self, incident_id: str) -> dict:
        incident = self._fetch_incident(incident_id)
        if not incident:
            return {}
        bundle = AuditEvidenceBundle.build(
            incident_id=str(incident.get("incident_id")),
            components={
                "incident": incident,
                "reviews": self._fetch_many("postmortem_reviews", "incident_id", str(incident.get("incident_id"))),
                "rca": self._fetch_many("postmortem_rca", "incident_id", str(incident.get("incident_id"))),
                "action_items": self._fetch_many("postmortem_action_items", "incident_id", str(incident.get("incident_id"))),
                "feedback": self._fetch_many("postmortem_feedback", "incident_id", str(incident.get("incident_id"))),
                "dispatch": self._fetch_dispatch(str(incident.get("incident_id"))),
                "approvals": self._fetch_approval_evidence(str(incident.get("incident_id"))),
            },
            previous_hash=self._latest_chain_hash(),
        )
        row = bundle.to_row()
        self.store.append("governance_audit_bundles", row)
        return row

    def latest_bundle_for_incident(self, incident_id: str) -> dict:
        return self.store.fetchone_dict(
            """
            SELECT *
            FROM governance_audit_bundles
            WHERE incident_id=?
            ORDER BY created_at DESC, bundle_id DESC
            LIMIT 1
            """,
            [incident_id],
        ) or {}

    def latest(self, limit: int = 20) -> list[dict]:
        return self.store.fetchall_dict(
            "SELECT * FROM governance_audit_bundles ORDER BY created_at DESC LIMIT ?",
            [max(int(limit), 1)],
        )

    def _fetch_incident(self, incident_id: str) -> dict:
        return self.store.fetchone_dict(
            "SELECT * FROM postmortem_incidents WHERE incident_id=? OR source_event_id=? ORDER BY created_at DESC LIMIT 1",
            [incident_id, incident_id],
        ) or {}

    def _fetch_many(self, table: str, key: str, value: str) -> list[dict]:
        return self.store.fetchall_dict(
            f"SELECT * FROM {table} WHERE {key}=? ORDER BY created_at ASC",
            [value],
        )

    def _fetch_dispatch(self, incident_id: str) -> list[dict]:
        return self.store.fetchall_dict(
            """
            SELECT d.*
            FROM postmortem_feedback_dispatch d
            JOIN postmortem_feedback f ON d.feedback_id = f.feedback_id
            WHERE f.incident_id=?
            ORDER BY d.created_at ASC
            """,
            [incident_id],
        )

    def _fetch_approval_evidence(self, incident_id: str) -> list[dict]:
        feedback = self._fetch_many("postmortem_feedback", "incident_id", incident_id)
        feedback_ids = [str(item.get("feedback_id")) for item in feedback if item.get("feedback_id")]
        approvals: list[dict] = []
        for feedback_id in feedback_ids:
            approvals.extend(
                self.store.fetchall_dict(
                    """
                    SELECT *
                    FROM pending_approvals
                    WHERE source_system='AFG-04'
                      AND (source_event_id=? OR idempotency_key=?)
                    ORDER BY created_at ASC
                    """,
                    [feedback_id, f"{feedback_id}:{self._target_for_feedback(feedback_id, feedback)}:{self._type_for_feedback(feedback_id, feedback)}"],
                )
            )
        approvals.extend(
            self.store.fetchall_dict(
                """
                SELECT *
                FROM pending_approvals
                WHERE source_system='AFG-04'
                  AND target_id=?
                ORDER BY created_at ASC
                """,
                [incident_id],
            )
        )
        unique: dict[str, dict] = {}
        for approval in approvals:
            unique[str(approval.get("approval_id"))] = approval
        return list(unique.values())

    def _target_for_feedback(self, feedback_id: str, feedback: list[dict]) -> str:
        for item in feedback:
            if item.get("feedback_id") == feedback_id:
                return str(item.get("target_system") or "")
        return ""

    def _type_for_feedback(self, feedback_id: str, feedback: list[dict]) -> str:
        for item in feedback:
            if item.get("feedback_id") == feedback_id:
                return str(item.get("feedback_type") or "")
        return ""

    def _latest_chain_hash(self) -> str:
        row = self.store.fetchone_dict(
            """
            SELECT chain_hash
            FROM governance_audit_bundles
            ORDER BY created_at DESC, bundle_id DESC
            LIMIT 1
            """
        )
        return str(row.get("chain_hash") or "") if row else ""

