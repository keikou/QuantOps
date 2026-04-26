from __future__ import annotations

from pathlib import Path

from ai_hedge_bot.core.clock import utc_now_iso
from ai_hedge_bot.core.ids import new_run_id
from ai_hedge_bot.governance_audit.models import sha256_json, stable_json


class AuditExportService:
    def __init__(self, store, export_dir: Path) -> None:
        self.store = store
        self.export_dir = export_dir

    def export_bundle(self, bundle: dict) -> dict:
        if not bundle:
            return {}
        self.export_dir.mkdir(parents=True, exist_ok=True)
        export_path = self.export_dir / f"{bundle.get('bundle_id')}.json"
        export_payload = stable_json(bundle)
        export_path.write_text(export_payload, encoding="utf-8")
        row = {
            "export_id": new_run_id().replace("run_", "audit_export_", 1),
            "bundle_id": bundle.get("bundle_id"),
            "incident_id": bundle.get("incident_id"),
            "exported_at": utc_now_iso(),
            "export_path": str(export_path),
            "export_hash": sha256_json(bundle),
        }
        self.store.append("governance_audit_exports", row)
        return row

    def latest(self, limit: int = 20) -> list[dict]:
        return self.store.fetchall_dict("SELECT * FROM governance_audit_exports ORDER BY exported_at DESC LIMIT ?", [max(int(limit), 1)])

