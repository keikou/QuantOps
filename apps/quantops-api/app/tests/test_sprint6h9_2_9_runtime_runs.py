from __future__ import annotations

import asyncio
from pathlib import Path

from app.services.command_center_service import CommandCenterService


class _RuntimeRunsV12Client:
    async def get_runtime_runs(self, limit: int = 20) -> dict:
        return {
            "items": [
                {
                    "run_id": "run-blocked",
                    "started_at": "2026-03-23T01:00:00+00:00",
                    "finished_at": "2026-03-23T01:00:04+00:00",
                    "status": "ok",
                    "duration_ms": 4000,
                    "triggered_by": "smoke",
                    "created_at": "2026-03-23T01:00:00+00:00",
                },
                {
                    "run_id": "run-filled",
                    "started_at": "2026-03-23T00:50:00+00:00",
                    "finished_at": "2026-03-23T00:50:03+00:00",
                    "status": "ok",
                    "duration_ms": 3000,
                    "triggered_by": "smoke",
                    "created_at": "2026-03-23T00:50:00+00:00",
                },
            ][:limit]
        }

    async def get_execution_bridge_by_run(self, run_id: str) -> dict:
        if run_id == "run-blocked":
            return {
                "run_id": run_id,
                "cycle_id": "cycle-blocked",
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
                "operator_message": "No trade was needed.",
                "last_transition_at": "2026-03-23T01:00:04+00:00",
            }
        return {
            "run_id": run_id,
            "cycle_id": "cycle-filled",
            "bridge_state": "filled",
            "planned_count": 2,
            "submitted_count": 2,
            "blocked_count": 0,
            "filled_count": 2,
            "event_chain_complete": True,
            "latest_reason_code": "",
            "latest_reason_summary": "",
            "blocking_component": "",
            "degraded_flags": ["stale_market_data"],
            "operator_message": "Orders filled successfully.",
            "last_transition_at": "2026-03-23T00:50:03+00:00",
        }

    async def get_execution_plans_by_run(self, run_id: str) -> dict:
        if run_id == "run-blocked":
            return {
                "run_id": run_id,
                "cycle_id": "cycle-blocked",
                "planner_status": "blocked",
                "generated_at": "2026-03-23T01:00:02+00:00",
                "items": [],
            }
        return {
            "run_id": run_id,
            "cycle_id": "cycle-filled",
            "planner_status": "generated",
            "generated_at": "2026-03-23T00:50:01+00:00",
            "items": [{"symbol": "BTCUSDT"}],
        }

    async def get_runtime_events_by_run(self, run_id: str, limit: int = 25) -> dict:
        if run_id == "run-blocked":
            return {
                "items": [
                    {
                        "run_id": run_id,
                        "event_type": "cycle_completed",
                        "status": "ok",
                        "severity": "info",
                        "summary": "Cycle completed.",
                        "timestamp": "2026-03-23T01:00:04+00:00",
                    }
                ][:limit]
            }
        return {
            "items": [
                {
                    "run_id": run_id,
                    "event_type": "fill_recorded",
                    "status": "ok",
                    "severity": "info",
                    "summary": "Fill recorded.",
                    "timestamp": "2026-03-23T00:50:02+00:00",
                },
                {
                    "run_id": run_id,
                    "event_type": "cycle_completed",
                    "status": "ok",
                    "severity": "info",
                    "summary": "Cycle completed.",
                    "timestamp": "2026-03-23T00:50:03+00:00",
                },
            ][:limit]
        }

    async def get_runtime_reasons_by_run(self, run_id: str, limit: int = 10) -> dict:
        if run_id == "run-blocked":
            return {
                "items": [
                    {
                        "run_id": run_id,
                        "reason_code": "NO_POSITION_DELTA",
                        "summary": "Planner produced no actionable delta.",
                        "details": {"blocking_component": "execution_planner"},
                    }
                ][:limit]
            }
        return {"items": []}


def _build_service() -> CommandCenterService:
    return CommandCenterService(
        v12_client=_RuntimeRunsV12Client(),  # type: ignore[arg-type]
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


def test_runtime_runs_returns_recent_rows_with_consistent_semantics() -> None:
    payload = asyncio.run(_build_service().get_runtime_runs(limit=10))

    assert payload["count"] == 2
    assert [item["run_id"] for item in payload["items"]] == ["run-blocked", "run-filled"]

    first = payload["items"][0]
    assert first["operator_state"] == "blocked"
    assert first["bridge_state"] == "planned_blocked"
    assert first["latest_reason_code"] == "NO_POSITION_DELTA"
    assert first["event_chain_complete"] is True
    assert first["detail_path"] == "/execution/runs/run-blocked"

    second = payload["items"][1]
    assert second["operator_state"] == "filled"
    assert second["filled_count"] == 2
    assert second["degraded"] is True
    assert second["last_successful_fill_at"] == "2026-03-23T00:50:02+00:00"


def test_runtime_runs_filters_on_operator_state_and_reason_code() -> None:
    payload = asyncio.run(
        _build_service().get_runtime_runs(
            limit=10,
            operator_state="blocked",
            reason_code="NO_POSITION_DELTA",
        )
    )

    assert payload["count"] == 1
    assert [item["run_id"] for item in payload["items"]] == ["run-blocked"]
    assert payload["filters"]["operator_state"] == "blocked"
    assert payload["filters"]["reason_code"] == "NO_POSITION_DELTA"


def test_runtime_runs_filters_on_blocking_component_and_artifact_availability(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "runtime_diagnostics"
    artifact_dir.mkdir()
    artifact_file = artifact_dir / "20260323-010000_run-blocked.json"
    artifact_file.write_text('{"run_id":"run-blocked"}', encoding="utf-8")

    original_root = CommandCenterService.ARTIFACT_ROOT
    CommandCenterService.ARTIFACT_ROOT = artifact_dir
    try:
        payload = asyncio.run(
            _build_service().get_runtime_runs(
                limit=10,
                blocking_component="execution_planner",
                artifact_available=True,
            )
        )
    finally:
        CommandCenterService.ARTIFACT_ROOT = original_root

    assert payload["count"] == 1
    assert [item["run_id"] for item in payload["items"]] == ["run-blocked"]
    assert payload["items"][0]["artifact_available"] is True
    assert payload["filters"]["blocking_component"] == "execution_planner"
    assert payload["filters"]["artifact_available"] is True
