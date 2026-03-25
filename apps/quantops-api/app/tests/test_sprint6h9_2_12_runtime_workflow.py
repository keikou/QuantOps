from __future__ import annotations

import asyncio

import pytest

from app.repositories.audit_repository import AuditRepository
from app.repositories.duckdb import DuckDBConnectionFactory
from app.repositories.runtime_workflow_repository import RuntimeWorkflowRepository
from app.security.rbac import RequestActor
from app.services.command_center_service import CommandCenterService


class _RuntimeWorkflowV12Client:
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
                    "degraded_flags": [],
                    "operator_message": "Orders filled successfully.",
                    "last_transition_at": "2026-03-23T00:56:03+00:00",
                    "last_successful_fill_at": "2026-03-23T00:56:02+00:00",
                    "planner_status": "generated",
                },
            ][:limit]
        }

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

    async def get_runtime_run(self, run_id: str) -> dict:
        return {
            "item": {
                "run_id": run_id,
                "job_name": "runtime_run_once",
                "mode": "paper",
                "started_at": "2026-03-23T00:00:01+00:00",
                "finished_at": "2026-03-23T00:00:05+00:00",
                "status": "success",
                "duration_ms": 4000,
                "triggered_by": "api",
                "checkpoints": [],
                "audit_logs": [],
            }
        }


def _build_service(tmp_path) -> CommandCenterService:
    factory = DuckDBConnectionFactory(str(tmp_path / "quantops.duckdb"))
    return CommandCenterService(
        v12_client=_RuntimeWorkflowV12Client(),  # type: ignore[arg-type]
        dashboard_service=None,  # type: ignore[arg-type]
        portfolio_service=None,  # type: ignore[arg-type]
        risk_service=None,  # type: ignore[arg-type]
        analytics_service=None,  # type: ignore[arg-type]
        monitoring_service=None,  # type: ignore[arg-type]
        alert_service=None,  # type: ignore[arg-type]
        scheduler_service=None,  # type: ignore[arg-type]
        control_service=None,  # type: ignore[arg-type]
        analytics_repository=None,  # type: ignore[arg-type]
        audit_repository=AuditRepository(factory),
        risk_repository=None,  # type: ignore[arg-type]
        notification_service=None,  # type: ignore[arg-type]
        runtime_workflow_repository=RuntimeWorkflowRepository(factory),
    )


def test_runtime_run_review_persists_and_surfaces_in_runs_and_debug(tmp_path) -> None:
    service = _build_service(tmp_path)
    actor = RequestActor(user_id="alice", role="operator")

    asyncio.run(
        service.review_runtime_run(
            run_id="run-blocked-new",
            review_status="investigating",
            acknowledged=True,
            operator_note="Checking planner handoff.",
            actor=actor,
        )
    )

    runs_payload = asyncio.run(service.get_runtime_runs(limit=10, window_minutes=30))
    first = runs_payload["items"][0]
    assert first["review_status"] == "investigating"
    assert first["acknowledged"] is True
    assert first["review"]["operator_note"] == "Checking planner handoff."
    assert first["review"]["reviewed_by"] == "alice"

    debug_payload = asyncio.run(service.get_runtime_debug(run_id="run-blocked-new"))
    assert debug_payload["review"]["review_status"] == "investigating"
    assert debug_payload["review"]["acknowledged"] is True


def test_runtime_issue_acknowledgement_surfaces_in_issue_bucket(tmp_path) -> None:
    service = _build_service(tmp_path)
    actor = RequestActor(user_id="bob", role="operator")

    asyncio.run(
        service.acknowledge_runtime_issue(
            diagnosis_code="execution_bridge_missing",
            note="Known transient issue during smoke runs.",
            actor=actor,
        )
    )

    issues_payload = asyncio.run(service.get_runtime_issues(limit=10, window_minutes=30))
    first = issues_payload["items"][0]
    assert first["code"] == "execution_bridge_missing"
    assert first["acknowledged"] is True
    assert first["acknowledgement"]["acknowledged_by"] == "bob"
    assert first["acknowledgement"]["note"] == "Known transient issue during smoke runs."


def test_runtime_review_requires_note_before_resolve(tmp_path) -> None:
    service = _build_service(tmp_path)
    actor = RequestActor(user_id="alice", role="operator")

    asyncio.run(
        service.review_runtime_run(
            run_id="run-blocked-new",
            review_status="investigating",
            acknowledged=True,
            operator_note="Investigating before resolve.",
            actor=actor,
        )
    )

    with pytest.raises(Exception) as exc:
        asyncio.run(
            service.review_runtime_run(
                run_id="run-blocked-new",
                review_status="resolved",
                acknowledged=True,
                operator_note="",
                actor=actor,
            )
        )

    assert "operator_note is required" in str(exc.value)


def test_runtime_review_rejects_invalid_transition_and_exposes_linked_evidence(tmp_path) -> None:
    service = _build_service(tmp_path)
    actor = RequestActor(user_id="alice", role="operator")

    asyncio.run(
        service.review_runtime_run(
            run_id="run-blocked-new",
            review_status="acknowledged",
            acknowledged=True,
            operator_note="Acknowledged for follow-up.",
            actor=actor,
        )
    )

    with pytest.raises(Exception) as exc:
        asyncio.run(
            service.review_runtime_run(
                run_id="run-blocked-new",
                review_status="resolved",
                acknowledged=True,
                operator_note="Closing without investigation should fail.",
                actor=actor,
            )
        )
    assert "invalid review transition" in str(exc.value)

    debug_payload = asyncio.run(service.get_runtime_debug(run_id="run-blocked-new"))
    assert debug_payload["review"]["allowed_transitions"] == ["new", "investigating", "ignored"]
    assert debug_payload["linked_evidence"]["execution_issue_path"] == "/execution?issueCode=execution_bridge_missing"
    assert "issue_code=execution_bridge_missing" in debug_payload["linked_evidence"]["runtime_runs_api_path"]
