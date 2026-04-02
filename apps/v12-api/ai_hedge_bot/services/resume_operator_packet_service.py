from __future__ import annotations

from pathlib import Path
from typing import Any

from ai_hedge_bot.services.hardening_handover_manifest_service import HardeningHandoverManifestService


class ResumeOperatorPacketService:
    DOC_NAME = "Resume_operator_packet_latest.md"

    def __init__(self) -> None:
        self.manifest_service = HardeningHandoverManifestService()
        self.repo_root = Path(__file__).resolve().parents[4]
        self.docs_root = self.repo_root / "docs"
        self.docs_root.mkdir(parents=True, exist_ok=True)

    def _build_summary(self) -> dict[str, Any]:
        manifest = self.manifest_service.build()
        artifacts = manifest.get("artifacts") or {}
        status_artifact = artifacts.get("hardening_status") or {}
        overall = status_artifact.get("overall") or {}
        return {
            "status": "ok",
            "track": manifest.get("track"),
            "branch_expectation": manifest.get("branch_expectation"),
            "latest_runtime_run_id": manifest.get("latest_runtime_run_id"),
            "overall_ready": manifest.get("overall_ready"),
            "ready_packet_count": overall.get("ready_packet_count"),
            "total_packet_count": overall.get("total_packet_count"),
            "consistency": manifest.get("consistency") or {},
            "docs": manifest.get("docs") or {},
            "scripts": manifest.get("scripts") or {},
            "artifacts": artifacts,
        }

    def _render(self, summary: dict[str, Any]) -> str:
        docs = summary.get("docs") or {}
        scripts = summary.get("scripts") or {}
        artifacts = summary.get("artifacts") or {}
        consistency = summary.get("consistency") or {}
        return "\n".join(
            [
                "# Resume Operator Packet Latest",
                "",
                f"Track: `{summary.get('track')}`",
                f"Branch: `{summary.get('branch_expectation')}`",
                f"Latest Runtime Run: `{summary.get('latest_runtime_run_id')}`",
                f"Packets Ready: `{summary.get('ready_packet_count')}` / `{summary.get('total_packet_count')}`",
                f"Overall Ready: `{summary.get('overall_ready')}`",
                "",
                "## Core Entry Points",
                "",
                f"- Auto resume handover: `{docs.get('auto_resume_handover')}`",
                f"- Architect handoff: `{docs.get('architect_handoff_latest')}`",
                f"- Snapshot: `{(artifacts.get('evidence_snapshot') or {}).get('path')}`",
                "",
                "## Recommended Verifiers",
                "",
                f"- hardening status: `{scripts.get('verify_hardening_status_surface')}`",
                f"- evidence snapshot: `{scripts.get('verify_hardening_evidence_snapshot')}`",
                f"- architect handoff: `{scripts.get('verify_hardening_architect_handoff')}`",
                "",
                "## Readiness",
                "",
                f"- snapshot available: `{consistency.get('snapshot_available')}`",
                f"- handoff available: `{consistency.get('handoff_available')}`",
                f"- reference files exist: `{consistency.get('all_reference_files_exist')}`",
                f"- operator ready: `{consistency.get('operator_ready')}`",
            ]
        )

    def save(self) -> dict[str, Any]:
        summary = self._build_summary()
        content = self._render(summary)
        path = self.docs_root / self.DOC_NAME
        path.write_text(content, encoding="utf-8")
        return {"status": "ok", "path": str(path), "content": content}

    def latest(self) -> dict[str, Any]:
        path = self.docs_root / self.DOC_NAME
        if not path.exists():
            return {"status": "missing", "path": str(path)}
        return {"status": "ok", "path": str(path), "content": path.read_text(encoding="utf-8")}
