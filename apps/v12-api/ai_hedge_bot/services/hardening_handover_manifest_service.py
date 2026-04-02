from __future__ import annotations

from pathlib import Path
from typing import Any

from ai_hedge_bot.services.hardening_architect_handoff_service import HardeningArchitectHandoffService
from ai_hedge_bot.services.hardening_evidence_snapshot_service import HardeningEvidenceSnapshotService
from ai_hedge_bot.services.hardening_status_service import HardeningStatusService


class HardeningHandoverManifestService:
    def __init__(self) -> None:
        self.hardening_status = HardeningStatusService()
        self.snapshot_service = HardeningEvidenceSnapshotService()
        self.handoff_service = HardeningArchitectHandoffService()
        self.repo_root = Path(__file__).resolve().parents[4]

    def build(self) -> dict[str, Any]:
        status_payload = self.hardening_status.build()
        snapshot_payload = self.snapshot_service.load()
        handoff_payload = self.handoff_service.latest()

        docs = {
            "auto_resume_handover": str(self.repo_root / "docs" / "Auto_resume_handover_2026-04-02.md"),
            "auto_resume_handover_legacy": str(self.repo_root / "docs" / "Auto_resume_handover_2026-03-29.md"),
            "hardening_status_update": str(self.repo_root / "docs" / "Post_Phase7_hardening_status_update_2026-04-01.md"),
            "architect_handoff_latest": str(self.repo_root / "docs" / "Hardening_architect_handoff_latest.md"),
            "handover_manifest_plan": str(self.repo_root / "docs" / "Hardening_handover_manifest_plan.md"),
        }
        scripts = {
            "verify_hardening_status_surface": str(self.repo_root / "test_bundle" / "scripts" / "verify_hardening_status_surface.py"),
            "verify_hardening_evidence_snapshot": str(self.repo_root / "test_bundle" / "scripts" / "verify_hardening_evidence_snapshot.py"),
            "verify_hardening_architect_handoff": str(self.repo_root / "test_bundle" / "scripts" / "verify_hardening_architect_handoff.py"),
        }
        surfaces = {
            "hardening_status": "/system/hardening-status",
            "operator_diagnostic_bundle": "/system/operator-diagnostic-bundle",
            "recovery_replay_diagnostic_bundle": "/system/recovery-replay-diagnostic-bundle",
            "hardening_evidence_snapshot_save": "/system/hardening-evidence-snapshot/save",
            "hardening_evidence_snapshot_latest": "/system/hardening-evidence-snapshot/latest",
            "hardening_architect_handoff_save": "/system/hardening-architect-handoff/save",
            "hardening_architect_handoff_latest": "/system/hardening-architect-handoff/latest",
            "hardening_handover_manifest": "/system/hardening-handover-manifest",
        }

        all_refs_exist = all(Path(value).exists() for value in docs.values() if value.endswith(".md"))
        all_refs_exist = all_refs_exist and all(Path(value).exists() for value in scripts.values())

        return {
            "status": "ok",
            "track": "System Reliability Hardening Track",
            "branch_expectation": "codex/post-phase7-hardening",
            "latest_runtime_run_id": status_payload.get("latest_runtime_run_id"),
            "overall_ready": (status_payload.get("overall") or {}).get("all_ready"),
            "docs": docs,
            "scripts": scripts,
            "surfaces": surfaces,
            "artifacts": {
                "hardening_status": {
                    "status": status_payload.get("status"),
                    "overall": status_payload.get("overall"),
                },
                "evidence_snapshot": {
                    "status": snapshot_payload.get("status"),
                    "path": snapshot_payload.get("path") or str(self.repo_root / "runtime" / "snapshots" / "hardening_evidence_latest.json"),
                },
                "architect_handoff": {
                    "status": handoff_payload.get("status"),
                    "path": handoff_payload.get("path") or str(self.repo_root / "docs" / "Hardening_architect_handoff_latest.md"),
                },
            },
            "consistency": {
                "all_reference_files_exist": all_refs_exist,
                "snapshot_available": snapshot_payload.get("status") == "ok",
                "handoff_available": handoff_payload.get("status") == "ok",
                "operator_ready": bool((status_payload.get("overall") or {}).get("all_ready")) and all_refs_exist,
            },
        }
