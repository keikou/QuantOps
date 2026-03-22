from __future__ import annotations

import asyncio
from pathlib import Path

from app.services.command_center_service import CommandCenterService


class _RuntimeDetailV12Client:
    async def get_execution_bridge_by_run(self, run_id: str) -> dict:
        return {
            "run_id": run_id,
            "cycle_id": "cycle-014a",
            "bridge_state": "planned_blocked",
            "planned_count": 1,
            "submitted_count": 0,
            "blocked_count": 1,
            "filled_count": 0,
            "event_chain_complete": True,
            "latest_reason_code": "NO_POSITION_DELTA",
            "latest_reason_summary": "Planner produced no actionable delta.",
            "blocking_component": "execution_planner",
            "degraded_flags": [],
            "operator_message": "No trade was required for this run.",
            "last_transition_at": "2026-03-23T00:00:05+00:00",
        }

    async def get_execution_plans_by_run(self, run_id: str) -> dict:
        return {
            "run_id": run_id,
            "cycle_id": "cycle-014a",
            "planner_status": "blocked",
            "generated_at": "2026-03-23T00:00:03+00:00",
            "items": [],
        }

    async def get_runtime_events_by_run(self, run_id: str, limit: int = 50) -> dict:
        return {
            "items": [
                {
                    "run_id": run_id,
                    "event_type": "cycle_started",
                    "status": "ok",
                    "severity": "info",
                    "summary": "Cycle started.",
                    "timestamp": "2026-03-23T00:00:01+00:00",
                },
                {
                    "run_id": run_id,
                    "event_type": "order_blocked",
                    "status": "blocked",
                    "severity": "info",
                    "summary": "Order blocked because there was no actionable delta.",
                    "reason_code": "NO_POSITION_DELTA",
                    "timestamp": "2026-03-23T00:00:04+00:00",
                },
                {
                    "run_id": run_id,
                    "event_type": "cycle_completed",
                    "status": "ok",
                    "severity": "info",
                    "summary": "Cycle completed.",
                    "timestamp": "2026-03-23T00:00:05+00:00",
                },
            ]
        }

    async def get_runtime_reasons_by_run(self, run_id: str, limit: int = 20) -> dict:
        return {
            "items": [
                {
                    "run_id": run_id,
                    "event_type": "order_blocked",
                    "reason_code": "NO_POSITION_DELTA",
                    "summary": "Planner produced no actionable delta.",
                    "details": {"blocking_component": "execution_planner"},
                }
            ]
        }


def _build_service() -> CommandCenterService:
    return CommandCenterService(
        v12_client=_RuntimeDetailV12Client(),  # type: ignore[arg-type]
        dashboard_service=None,  # type: ignore[arg-type]
        portfolio_service=None,  # type: ignore[arg-type]
        risk_service=None,  # type: ignore[arg-type]
        analytics_service=None,  # type: ignore[arg-type]
        monitoring_service=None,  # type: ignore[arg-type]
        alert_service=None,  # type: ignore[arg-type]
        scheduler_service=None,  # type: ignore[arg-type]
        control_service=None,  # type: ignore[arg-type]
        analytics_repository=None,  # type: ignore[arg-type]
        audit_repository=None,  # type: ignore[arg-type]
        risk_repository=None,  # type: ignore[arg-type]
        notification_service=None,  # type: ignore[arg-type]
    )


def test_command_center_runtime_debug_uses_run_scoped_events() -> None:
    payload = asyncio.run(_build_service().get_runtime_debug(run_id="run-014a"))

    assert payload["status"] == "ok"
    assert payload["summary"]["run_id"] == "run-014a"
    assert payload["summary"]["operator_state"] == "blocked"
    assert payload["summary"]["latest_reason_code"] == "NO_POSITION_DELTA"
    assert payload["summary"]["last_cycle_completed_at"] == "2026-03-23T00:00:05+00:00"
    assert len(payload["timeline"]) == 3
    assert payload["raw"]["events"][1]["event_type"] == "order_blocked"


def test_command_center_runtime_debug_includes_artifact_bundle_when_present(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "runtime_diagnostics"
    artifact_dir.mkdir()
    artifact_file = artifact_dir / "20260323-000000_run-014a.json"
    artifact_file.write_text('{"run_id":"run-014a"}', encoding="utf-8")

    original_root = CommandCenterService.ARTIFACT_ROOT
    CommandCenterService.ARTIFACT_ROOT = artifact_dir
    try:
        payload = asyncio.run(_build_service().get_runtime_debug(run_id="run-014a"))
    finally:
        CommandCenterService.ARTIFACT_ROOT = original_root

    artifact = payload["provenance"]["artifact_bundle"]
    assert artifact["run_id"] == "run-014a"
    assert artifact["name"] == artifact_file.name
    assert artifact["path"] == str(artifact_file)
