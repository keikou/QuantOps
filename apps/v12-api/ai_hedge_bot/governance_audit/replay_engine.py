from __future__ import annotations

from ai_hedge_bot.core.clock import utc_now_iso
from ai_hedge_bot.core.ids import new_run_id
from ai_hedge_bot.governance_audit.hash_verifier import HashVerifier
from ai_hedge_bot.governance_audit.models import ReplayResult, parse_json, stable_json
from ai_hedge_bot.governance_audit.trace_builder import TraceBuilder


class GovernanceReplayEngine:
    def __init__(self, store) -> None:
        self.store = store
        self.hash_verifier = HashVerifier()
        self.trace_builder = TraceBuilder()

    def replay_incident(self, incident_id: str) -> dict:
        bundle = self.store.fetchone_dict(
            """
            SELECT *
            FROM governance_audit_bundles
            WHERE incident_id=?
            ORDER BY created_at DESC, bundle_id DESC
            LIMIT 1
            """,
            [incident_id],
        ) or {}
        if not bundle:
            return {}
        return self.replay_bundle(str(bundle.get("bundle_id")))

    def replay_bundle(self, bundle_id: str) -> dict:
        started_at = utc_now_iso()
        bundle = self.store.fetchone_dict("SELECT * FROM governance_audit_bundles WHERE bundle_id=? LIMIT 1", [bundle_id]) or {}
        if not bundle:
            return {}
        validation_errors: list[str] = []
        ok, hash_errors = self.hash_verifier.verify_bundle_row(bundle)
        validation_errors.extend(hash_errors)
        components = parse_json(bundle.get("content_json"), {})
        validation_errors.extend(self._validate_components(components))
        decision_trace = self.trace_builder.build_decision_trace(components)
        approval_trace = self.trace_builder.build_approval_trace(components)
        feedback_trace = self.trace_builder.build_feedback_trace(components)
        dispatch_trace = self.trace_builder.build_dispatch_trace(components)
        result = ReplayResult(
            replay_id=new_run_id().replace("run_", "replay_", 1),
            incident_id=str(bundle.get("incident_id")),
            bundle_id=str(bundle.get("bundle_id")),
            status="passed" if ok and not validation_errors else "failed",
            started_at=started_at,
            completed_at=utc_now_iso(),
            decision_trace=decision_trace,
            approval_trace=approval_trace,
            feedback_trace=feedback_trace,
            dispatch_trace=dispatch_trace,
            validation_errors=validation_errors,
        )
        self.store.append("governance_replay_logs", result.to_row())
        self._persist_traces(result)
        return result.to_dict()

    def latest_replay(self, replay_id: str) -> dict:
        return self.store.fetchone_dict("SELECT * FROM governance_replay_logs WHERE replay_id=? LIMIT 1", [replay_id]) or {}

    def latest(self, limit: int = 20) -> list[dict]:
        return self.store.fetchall_dict("SELECT * FROM governance_replay_logs ORDER BY started_at DESC LIMIT ?", [max(int(limit), 1)])

    def trace_latest(self, replay_id: str, limit: int = 100) -> list[dict]:
        return self.store.fetchall_dict(
            "SELECT * FROM governance_decision_trace WHERE replay_id=? ORDER BY sequence_no ASC LIMIT ?",
            [replay_id, max(int(limit), 1)],
        )

    def _validate_components(self, components: dict) -> list[str]:
        errors: list[str] = []
        if not components.get("incident"):
            errors.append("missing_incident_evidence")
        if not components.get("rca"):
            errors.append("missing_rca_evidence")
        approvals = components.get("approvals") or []
        for feedback in components.get("feedback") or []:
            if bool(feedback.get("requires_approval")) and not approvals:
                errors.append(f"missing_approval_evidence_for_feedback:{feedback.get('feedback_id')}")
        return errors

    def _persist_traces(self, result: ReplayResult) -> None:
        sequence_no = 0
        for trace_type, items in [
            ("decision", result.decision_trace),
            ("approval", result.approval_trace),
            ("feedback", result.feedback_trace),
            ("dispatch", result.dispatch_trace),
        ]:
            for item in items:
                self.store.append(
                    "governance_decision_trace",
                    {
                        "trace_id": new_run_id().replace("run_", "trace_", 1),
                        "replay_id": result.replay_id,
                        "trace_type": trace_type,
                        "sequence_no": sequence_no,
                        "event_json": stable_json(item),
                        "created_at": utc_now_iso(),
                    },
                )
                sequence_no += 1

