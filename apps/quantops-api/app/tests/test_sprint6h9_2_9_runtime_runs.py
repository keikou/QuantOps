from __future__ import annotations

import asyncio
from pathlib import Path

from app.services.command_center_service import CommandCenterService


class _RuntimeRunsV12Client:
    async def get_runtime_runs(self, limit: int = 20) -> dict:
        return {
            "items": [
                {
                    "run_id": "run-blocked-new",
                    "started_at": "2026-03-23T01:00:00+00:00",
                    "finished_at": "2026-03-23T01:00:04+00:00",
                    "status": "ok",
                    "duration_ms": 4000,
                    "triggered_by": "smoke",
                    "created_at": "2026-03-23T01:00:00+00:00",
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
                    "planner_status": "blocked",
                },
                {
                    "run_id": "run-blocked-mid",
                    "started_at": "2026-03-23T00:57:00+00:00",
                    "finished_at": "2026-03-23T00:57:04+00:00",
                    "status": "ok",
                    "duration_ms": 4000,
                    "triggered_by": "smoke",
                    "created_at": "2026-03-23T00:57:00+00:00",
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
                    "last_transition_at": "2026-03-23T00:57:04+00:00",
                    "planner_status": "blocked",
                },
                {
                    "run_id": "run-filled",
                    "started_at": "2026-03-23T00:56:00+00:00",
                    "finished_at": "2026-03-23T00:56:03+00:00",
                    "status": "ok",
                    "duration_ms": 3000,
                    "triggered_by": "smoke",
                    "created_at": "2026-03-23T00:56:00+00:00",
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
                    "last_transition_at": "2026-03-23T00:56:03+00:00",
                    "last_successful_fill_at": "2026-03-23T00:56:02+00:00",
                    "planner_status": "generated",
                },
                {
                    "run_id": "run-blocked-old",
                    "started_at": "2026-03-23T00:55:00+00:00",
                    "finished_at": "2026-03-23T00:55:04+00:00",
                    "status": "ok",
                    "duration_ms": 4000,
                    "triggered_by": "smoke",
                    "created_at": "2026-03-23T00:55:00+00:00",
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
                    "last_transition_at": "2026-03-23T00:55:04+00:00",
                    "planner_status": "blocked",
                },
                {
                    "run_id": "run-too-old",
                    "started_at": "2026-03-23T00:50:00+00:00",
                    "finished_at": "2026-03-23T00:50:03+00:00",
                    "status": "ok",
                    "duration_ms": 3000,
                    "triggered_by": "smoke",
                    "created_at": "2026-03-23T00:50:00+00:00",
                    "bridge_state": "filled",
                    "planned_count": 1,
                    "submitted_count": 1,
                    "blocked_count": 0,
                    "filled_count": 1,
                    "event_chain_complete": True,
                    "latest_reason_code": "",
                    "latest_reason_summary": "",
                    "blocking_component": "",
                    "degraded_flags": [],
                    "operator_message": "Outside default window.",
                    "last_transition_at": "2026-03-23T00:50:03+00:00",
                    "planner_status": "generated",
                },
            ][:limit]
        }


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


def test_runtime_runs_defaults_to_recent_five_minute_window() -> None:
    payload = asyncio.run(_build_service().get_runtime_runs(limit=10))

    assert payload["count"] == 4
    assert [item["run_id"] for item in payload["items"]] == ["run-blocked-new", "run-blocked-mid", "run-filled", "run-blocked-old"]
    assert payload["filters"]["window_minutes"] == 5


def test_runtime_runs_returns_recent_rows_with_consistent_semantics() -> None:
    payload = asyncio.run(_build_service().get_runtime_runs(limit=10, window_minutes=30))

    assert payload["count"] == 5

    first = payload["items"][0]
    assert first["operator_state"] == "blocked"
    assert first["bridge_state"] == "planned_blocked"
    assert first["latest_reason_code"] == "NO_POSITION_DELTA"
    assert first["diagnosis"]["primary_code"] == "execution_bridge_missing"
    assert first["event_chain_complete"] is True
    assert first["detail_path"] == "/execution/runs/run-blocked-new"

    third = payload["items"][2]
    assert third["operator_state"] == "filled"
    assert third["filled_count"] == 2
    assert third["degraded"] is True
    assert third["diagnosis"]["primary_code"] == "successful_chain"
    assert third["last_successful_fill_at"] == "2026-03-23T00:56:02+00:00"


def test_runtime_runs_filter_by_diagnosis_code() -> None:
    payload = asyncio.run(
        _build_service().get_runtime_runs(
            limit=10,
            window_minutes=30,
            issue_code="execution_bridge_missing",
        )
    )

    assert payload["count"] == 3
    assert [item["run_id"] for item in payload["items"]] == ["run-blocked-new", "run-blocked-mid", "run-blocked-old"]
    assert payload["filters"]["issue_code"] == "execution_bridge_missing"


def test_runtime_runs_filters_on_operator_state_and_reason_code() -> None:
    payload = asyncio.run(
        _build_service().get_runtime_runs(
            limit=10,
            window_minutes=30,
            operator_state="blocked",
            reason_code="NO_POSITION_DELTA",
        )
    )

    assert payload["count"] == 3
    assert [item["run_id"] for item in payload["items"]] == ["run-blocked-new", "run-blocked-mid", "run-blocked-old"]
    assert payload["filters"]["operator_state"] == "blocked"
    assert payload["filters"]["reason_code"] == "NO_POSITION_DELTA"


def test_runtime_runs_filters_on_blocking_component_and_artifact_availability(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "runtime_diagnostics"
    artifact_dir.mkdir()
    artifact_file = artifact_dir / "20260323-010000_run-blocked-new.json"
    artifact_file.write_text('{"run_id":"run-blocked-new"}', encoding="utf-8")

    original_root = CommandCenterService.ARTIFACT_ROOT
    CommandCenterService.ARTIFACT_ROOT = artifact_dir
    try:
        payload = asyncio.run(
            _build_service().get_runtime_runs(
                limit=10,
                window_minutes=30,
                blocking_component="execution_planner",
                artifact_available=True,
            )
        )
    finally:
        CommandCenterService.ARTIFACT_ROOT = original_root

    assert payload["count"] == 1
    assert [item["run_id"] for item in payload["items"]] == ["run-blocked-new"]
    assert payload["items"][0]["artifact_available"] is True
    assert payload["filters"]["blocking_component"] == "execution_planner"
    assert payload["filters"]["artifact_available"] is True


def test_runtime_issues_rollup_marks_repeating_and_trend() -> None:
    payload = asyncio.run(_build_service().get_runtime_issues(limit=10, window_minutes=30))

    assert payload["count"] == 2
    assert payload["items"][0]["code"] == "execution_bridge_missing"
    assert payload["items"][0]["count"] == 3
    assert payload["items"][0]["distinct_run_count"] == 3
    assert payload["items"][0]["recurrence_status"] == "persistent"
    assert payload["items"][0]["trend"] == "up"
    assert payload["items"][0]["window_run_count"] == 5
    assert payload["items"][0]["example_run_id"] == "run-blocked-new"

    assert payload["items"][1]["code"] == "successful_chain"
    assert payload["items"][1]["recurrence_status"] == "repeating"


def test_runtime_issues_rollup_window_metadata_present() -> None:
    payload = asyncio.run(_build_service().get_runtime_issues(limit=10, window_minutes=30))

    first = payload["items"][0]
    assert first["first_seen_at"] == "2026-03-23T00:55:04+00:00"
    assert first["last_seen_at"] == "2026-03-23T01:00:04+00:00"
    assert first["window_start"] == "2026-03-23T00:50:00+00:00"
    assert first["window_end"] == "2026-03-23T01:00:04+00:00"
