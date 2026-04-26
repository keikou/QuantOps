from __future__ import annotations

from ai_hedge_bot.app.container import CONTAINER
from ai_hedge_bot.governance_audit.audit_bundle_builder import AuditBundleBuilder
from ai_hedge_bot.governance_audit.export_service import AuditExportService
from ai_hedge_bot.governance_audit.hash_verifier import HashVerifier
from ai_hedge_bot.governance_audit.replay_engine import GovernanceReplayEngine


class GovernanceAuditService:
    def __init__(self) -> None:
        self.store = CONTAINER.runtime_store
        self.builder = AuditBundleBuilder(self.store)
        self.replay_engine = GovernanceReplayEngine(self.store)
        self.hash_verifier = HashVerifier()
        self.exporter = AuditExportService(self.store, CONTAINER.runtime_dir / "audit_exports")

    def build_bundle(self, incident_id: str) -> dict:
        bundle = self.builder.build_for_incident(incident_id)
        return {"status": "ok" if bundle else "not_found", "audit_bundle": bundle}

    def replay_incident(self, incident_id: str) -> dict:
        result = self.replay_engine.replay_incident(incident_id)
        return {"status": "ok" if result else "not_found", "replay": result}

    def replay(self, replay_id: str) -> dict:
        replay = self.replay_engine.latest_replay(replay_id)
        trace = self.replay_engine.trace_latest(replay_id) if replay else []
        return {"status": "ok" if replay else "not_found", "replay": replay, "trace": trace}

    def export(self, incident_id: str) -> dict:
        bundle = self.builder.latest_bundle_for_incident(incident_id)
        if not bundle:
            bundle = self.builder.build_for_incident(incident_id)
        export = self.exporter.export_bundle(bundle)
        return {"status": "ok" if export else "not_found", "export": export, "audit_bundle": bundle}

    def latest_bundles(self, limit: int = 20) -> dict:
        rows = self.builder.latest(limit=limit)
        return {"status": "ok", "items": rows, "audit_bundle_summary": {"bundle_count": len(rows)}}

    def latest_replays(self, limit: int = 20) -> dict:
        rows = self.replay_engine.latest(limit=limit)
        return {"status": "ok", "items": rows, "governance_replay_summary": {"replay_count": len(rows)}}

    def latest_exports(self, limit: int = 20) -> dict:
        rows = self.exporter.latest(limit=limit)
        return {"status": "ok", "items": rows, "audit_export_summary": {"export_count": len(rows)}}

