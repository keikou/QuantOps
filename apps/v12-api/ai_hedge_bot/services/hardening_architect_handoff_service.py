from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ai_hedge_bot.services.hardening_evidence_snapshot_service import HardeningEvidenceSnapshotService


class HardeningArchitectHandoffService:
    DOC_NAME = "Hardening_architect_handoff_latest.md"

    def __init__(self) -> None:
        self.snapshot_service = HardeningEvidenceSnapshotService()
        self.docs_root = Path(__file__).resolve().parents[4] / "docs"
        self.docs_root.mkdir(parents=True, exist_ok=True)

    def _render(self, payload: dict[str, Any]) -> str:
        generated_at = str(payload.get("generated_at") or datetime.now(timezone.utc).isoformat())
        hardening_status = payload.get("hardening_status") or {}
        overall = hardening_status.get("overall") or {}
        packets = hardening_status.get("packets") or []
        operator_bundle = payload.get("operator_diagnostic_bundle") or {}
        recovery_bundle = payload.get("recovery_replay_diagnostic_bundle") or {}
        operator_summary = operator_bundle.get("operator_summary") or {}
        operator_consistency = operator_bundle.get("consistency") or {}
        recovery_summary = recovery_bundle.get("recovery_summary") or {}
        recovery_consistency = recovery_bundle.get("consistency") or {}

        packet_lines = []
        for item in packets:
            packet_name = str(item.get("packet") or "")
            ready = "true" if bool(item.get("ready")) else "false"
            summary = str(item.get("summary") or "")
            packet_lines.append(f"- `{packet_name}`: ready=`{ready}`; {summary}")

        mismatch_lines = []
        for value in operator_consistency.get("mismatches") or []:
            mismatch_lines.append(f"- operator mismatch: `{value}`")
        for value in recovery_consistency.get("mismatches") or []:
            mismatch_lines.append(f"- recovery mismatch: `{value}`")
        if not mismatch_lines:
            mismatch_lines.append("- none")

        return "\n".join(
            [
                "# Hardening Architect Handoff Latest",
                "",
                f"Date: `{generated_at[:10]}`",
                "Repo: `QuantOps_github`",
                "Branch: `codex/post-phase7-hardening`",
                "Track: `System Reliability Hardening Track`",
                "Status: `generated_from_live_snapshot`",
                "",
                "## Summary",
                "",
                "Architect guidance remains unchanged:",
                "",
                "```text",
                "Do not name Phase8 yet.",
                "Keep this as System Reliability Hardening Track.",
                "```",
                "",
                "Current live hardening snapshot says:",
                "",
                f"- overall status = `{overall.get('status')}`",
                f"- ready packets = `{overall.get('ready_packet_count')}` / `{overall.get('total_packet_count')}`",
                f"- all ready = `{overall.get('all_ready')}`",
                f"- latest runtime run = `{hardening_status.get('latest_runtime_run_id')}`",
                f"- latest recovery live order = `{hardening_status.get('latest_recovery_live_order_id')}`",
                "",
                "## Packet Readiness",
                "",
                *packet_lines,
                "",
                "## Operator Diagnostic Snapshot",
                "",
                f"- run_id = `{operator_bundle.get('run_id')}`",
                f"- cycle_id = `{operator_bundle.get('cycle_id')}`",
                f"- bridge_state = `{operator_summary.get('bridge_state')}`",
                f"- cycle_status = `{operator_summary.get('cycle_status')}`",
                f"- event_chain_complete = `{operator_summary.get('event_chain_complete')}`",
                f"- governance linked = `{operator_consistency.get('governance_linked')}`",
                f"- operator ready = `{operator_consistency.get('operator_ready')}`",
                "",
                "## Recovery / Replay Diagnostic Snapshot",
                "",
                f"- live_order_id = `{recovery_bundle.get('live_order_id')}`",
                f"- source_path = `{recovery_summary.get('source_path')}`",
                f"- order_status = `{recovery_summary.get('order_status')}`",
                f"- incident_status = `{recovery_summary.get('incident_status')}`",
                f"- trading_state = `{recovery_summary.get('trading_state')}`",
                f"- operator ready = `{recovery_consistency.get('operator_ready')}`",
                "",
                "## Open Mismatches",
                "",
                *mismatch_lines,
                "",
                "## Meaning",
                "",
                "This handoff is generated from the current hardening evidence snapshot, not from a manual status rewrite.",
                "It does not reopen any Phase1 to Phase7 closure claim.",
            ]
        )

    def save(self) -> dict[str, Any]:
        snapshot_payload = self.snapshot_service.build_payload()
        markdown = self._render(snapshot_payload)
        path = self.docs_root / self.DOC_NAME
        path.write_text(markdown, encoding="utf-8")
        return {
            "status": "ok",
            "path": str(path),
            "generated_at": snapshot_payload.get("generated_at"),
            "content": markdown,
        }

    def latest(self) -> dict[str, Any]:
        path = self.docs_root / self.DOC_NAME
        if not path.exists():
            return {"status": "missing", "path": str(path)}
        return {
            "status": "ok",
            "path": str(path),
            "content": path.read_text(encoding="utf-8"),
        }
