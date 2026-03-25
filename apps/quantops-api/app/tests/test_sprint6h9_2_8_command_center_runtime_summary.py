from __future__ import annotations

import asyncio
import time

from app.services.command_center_service import CommandCenterService


class _RuntimeV12Client:
    def __init__(self) -> None:
        self.bridge_calls = 0
        self.status_calls = 0
        self.plans_calls = 0

    async def get_runtime_status(self) -> dict:
        self.status_calls += 1
        return {
            "status": "ok",
            "run_id": "run-123",
            "cycle_id": "cycle-123",
            "bridge_state": "submitted_no_fill",
            "planned_count": 2,
            "submitted_count": 2,
            "blocked_count": 0,
            "filled_count": 0,
            "event_chain_complete": True,
            "latest_reason_code": "ORDER_REJECTED",
            "latest_reason_summary": "Orders submitted but no fills were recorded.",
            "blocking_component": "execution_bridge",
            "degraded_flags": ["stale_market_data"],
            "operator_message": "The cycle reached the market but did not fill.",
            "last_transition_at": "2026-03-23T00:00:09+00:00",
            "source_snapshot_time": "2026-03-23T00:00:09+00:00",
        }

    async def get_execution_bridge_latest(self) -> dict:
        self.bridge_calls += 1
        return {
            "status": "ok",
            "run_id": "run-123",
            "cycle_id": "cycle-123",
            "bridge_state": "submitted_no_fill",
            "planned_count": 2,
            "submitted_count": 2,
            "blocked_count": 0,
            "filled_count": 0,
            "event_chain_complete": True,
            "latest_reason_code": "ORDER_REJECTED",
            "latest_reason_summary": "Orders submitted but no fills were recorded.",
            "blocking_component": "execution_bridge",
            "degraded_flags": ["stale_market_data"],
            "operator_message": "The cycle reached the market but did not fill.",
            "last_transition_at": "2026-03-23T00:00:09+00:00",
        }

    async def get_execution_plans_latest(self) -> dict:
        self.plans_calls += 1
        return {
            "run_id": "run-123",
            "cycle_id": "cycle-123",
            "planner_status": "generated",
            "generated_at": "2026-03-23T00:00:02+00:00",
        }

    async def get_runtime_events_latest(self, limit: int = 20) -> dict:
        return {
            "items": [
                {
                    "event_type": "cycle_completed",
                    "summary": "Cycle completed.",
                    "severity": "info",
                    "status": "ok",
                    "timestamp": "2026-03-23T00:00:10+00:00",
                },
                {
                    "event_type": "portfolio_updated",
                    "summary": "Portfolio state updated.",
                    "severity": "info",
                    "status": "ok",
                    "timestamp": "2026-03-23T00:00:08+00:00",
                },
                {
                    "event_type": "fill_recorded",
                    "summary": "Latest successful fill from prior cycle.",
                    "severity": "info",
                    "status": "ok",
                    "timestamp": "2026-03-23T00:00:06+00:00",
                },
                {
                    "event_type": "order_submitted",
                    "summary": "Submitted order.",
                    "severity": "info",
                    "status": "ok",
                    "timestamp": "2026-03-23T00:00:05+00:00",
                },
            ]
        }

    async def get_runtime_reasons_latest(self, limit: int = 10) -> dict:
        return {
            "items": [
                {
                    "reason_code": "ORDER_REJECTED",
                    "summary": "Orders submitted but no fills were recorded.",
                    "details": {"blocking_component": "execution_bridge"},
                }
            ]
        }


class _SlowRuntimeV12Client(_RuntimeV12Client):
    async def get_execution_plans_latest(self) -> dict:
        await asyncio.sleep(0.3)
        return await super().get_execution_plans_latest()

    async def get_runtime_events_latest(self, limit: int = 20) -> dict:
        await asyncio.sleep(0.3)
        return await super().get_runtime_events_latest(limit=limit)

    async def get_runtime_reasons_latest(self, limit: int = 10) -> dict:
        await asyncio.sleep(0.3)
        return await super().get_runtime_reasons_latest(limit=limit)


class _CountingRuntimeService(CommandCenterService):
    def __init__(self) -> None:
        super().__init__(
            v12_client=_RuntimeV12Client(),  # type: ignore[arg-type]
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
        self.build_calls = 0

    async def _build_runtime_latest_live(self) -> dict:
        self.build_calls += 1
        await asyncio.sleep(0.05)
        return {
            "run_id": "run-123",
            "operator_state": "submitted_no_fill",
            "latest_reason_code": "ORDER_REJECTED",
            "last_transition_at": "2026-03-23T00:00:09+00:00",
            "as_of": "2026-03-23T00:00:10+00:00",
        }


def _build_service() -> CommandCenterService:
    return CommandCenterService(
        v12_client=_RuntimeV12Client(),  # type: ignore[arg-type]
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


def test_command_center_runtime_latest_exposes_operator_summary_fields() -> None:
    payload = asyncio.run(_build_service().get_runtime_latest())

    assert payload["run_id"] == "run-123"
    assert payload["operator_state"] == "submitted_no_fill"
    assert payload["build_status"] == "live"
    assert payload["rebuilt_at"]
    assert payload["source_snapshot_time"] == "2026-03-23T00:00:09+00:00"
    assert payload["degraded"] is True
    assert payload["latest_reason_code"] == "ORDER_REJECTED"
    assert payload["stable_value"]["operator_state"] == "submitted_no_fill"
    assert payload["display_value"]["latest_reason_code"] == "ORDER_REJECTED"
    assert payload["last_successful_fill_at"] is None
    assert payload["last_successful_portfolio_update_at"] is None
    assert payload["last_cycle_completed_at"] is None


def test_command_center_runtime_latest_bounds_auxiliary_reads() -> None:
    service = CommandCenterService(
        v12_client=_SlowRuntimeV12Client(),  # type: ignore[arg-type]
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
    service.RUNTIME_LATEST_PRIMARY_TIMEOUT_SECONDS = 0.08
    service.RUNTIME_LATEST_AUX_TIMEOUT_SECONDS = 0.08

    started = time.perf_counter()
    payload = asyncio.run(service.get_runtime_latest())
    elapsed = time.perf_counter() - started

    assert payload["run_id"] == "run-123"
    assert payload["operator_state"] == "submitted_no_fill"
    assert payload["build_status"] == "live"
    assert payload["rebuilt_at"]
    assert payload["latest_reason_code"] == "ORDER_REJECTED"
    assert payload["last_successful_fill_at"] is None
    assert payload["last_successful_portfolio_update_at"] is None
    assert payload["last_cycle_completed_at"] is None
    assert elapsed < 0.2


def test_command_center_runtime_latest_coalesces_concurrent_live_builds() -> None:
    service = _CountingRuntimeService()

    async def run_test() -> tuple[dict, dict]:
        return await asyncio.gather(service.get_runtime_latest(), service.get_runtime_latest())

    first, second = asyncio.run(run_test())

    assert first["run_id"] == "run-123"
    assert second["latest_reason_code"] == "ORDER_REJECTED"
    assert first["build_status"] == "live"
    assert first["rebuilt_at"]
    assert service.build_calls == 1


def test_command_center_runtime_latest_marks_stale_and_fresh_cache_responses() -> None:
    service = _CountingRuntimeService()
    service._runtime_latest_cache = {
        "run_id": "run-stale",
        "operator_state": "blocked",
        "latest_reason_code": "STALE_REASON",
        "last_transition_at": "2026-03-23T00:00:09+00:00",
        "source_snapshot_time": "2026-03-23T00:00:09+00:00",
        "as_of": "2026-03-23T00:00:10+00:00",
        "_cached_at": "2026-03-23T00:00:10+00:00",
    }

    stale_payload = asyncio.run(service.get_runtime_latest())
    assert stale_payload["build_status"] == "stale_cache"
    assert stale_payload["rebuilt_at"]

    fresh_source_iso = "2026-03-23T00:00:09+00:00"
    fresh_cached_iso = "2999-01-01T00:00:00+00:00"
    service._runtime_latest_cache = {
        "run_id": "run-fresh",
        "operator_state": "blocked",
        "latest_reason_code": "FRESH_REASON",
        "last_transition_at": fresh_source_iso,
        "source_snapshot_time": fresh_source_iso,
        "as_of": fresh_source_iso,
        "_cached_at": fresh_cached_iso,
    }

    fresh_payload = asyncio.run(service.get_runtime_latest())
    assert fresh_payload["build_status"] == "fresh_cache"
    assert fresh_payload["data_freshness_sec"] is not None


class _RuntimeSummaryPathClient(_RuntimeV12Client):
    def __init__(self) -> None:
        super().__init__()
        self.events_calls = 0
        self.reasons_calls = 0

    async def get_runtime_events_latest(self, limit: int = 20) -> dict:
        self.events_calls += 1
        return await super().get_runtime_events_latest(limit=limit)

    async def get_runtime_reasons_latest(self, limit: int = 10) -> dict:
        self.reasons_calls += 1
        return await super().get_runtime_reasons_latest(limit=limit)


def test_command_center_runtime_latest_skips_detail_upstreams_on_summary_path() -> None:
    client = _RuntimeSummaryPathClient()
    service = CommandCenterService(
        v12_client=client,  # type: ignore[arg-type]
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

    payload = asyncio.run(service.get_runtime_latest())

    assert payload["run_id"] == "run-123"
    assert payload["planner_status"] == "unknown"
    assert client.status_calls == 1
    assert client.bridge_calls == 0
    assert client.plans_calls == 0
    assert client.events_calls == 0
    assert client.reasons_calls == 0


def test_command_center_runtime_latest_refresh_has_cooldown() -> None:
    service = _CountingRuntimeService()
    service._runtime_latest_cache = {
        "run_id": "run-stale",
        "operator_state": "blocked",
        "latest_reason_code": "STALE_REASON",
        "last_transition_at": "2026-03-23T00:00:09+00:00",
        "source_snapshot_time": "2026-03-23T00:00:09+00:00",
        "as_of": "2026-03-23T00:00:10+00:00",
        "_cached_at": "2026-03-23T00:00:10+00:00",
    }
    service._runtime_latest_refresh_requested_at = "2999-01-01T00:00:00+00:00"

    first = asyncio.run(service.get_runtime_latest())
    second = asyncio.run(service.get_runtime_latest())

    assert first["build_status"] == "stale_cache"
    assert second["build_status"] == "stale_cache"
    assert service.build_calls == 0
