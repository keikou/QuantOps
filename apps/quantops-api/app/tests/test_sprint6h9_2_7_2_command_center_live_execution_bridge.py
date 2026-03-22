from __future__ import annotations

import asyncio

from app.services.command_center_service import CommandCenterService


class _DashboardService:
    async def get_overview(self) -> dict:
        return {
            "portfolio_value": 101250.0,
            "pnl": 1250.0,
            "gross_exposure": 1.1,
            "net_exposure": 0.2,
            "active_strategies": 3,
            "as_of": "2026-03-22T00:00:00+00:00",
        }


class _RiskService:
    async def get_snapshot(self) -> dict:
        return {
            "trading_state": "running",
            "kill_switch": "normal",
            "alert_state": "ok",
            "as_of": "2026-03-22T00:00:00+00:00",
        }


class _MonitoringService:
    async def get_system(self) -> dict:
        return {
            "status": "ok",
            "executionState": "executing",
            "executionReason": "recent_execution_activity",
            "worker_status": "ok",
            "as_of": "2026-03-22T00:00:00+00:00",
        }


class _AlertService:
    def list_alerts(self) -> dict:
        return {"open_count": 1}


class _SchedulerService:
    def list_jobs(self) -> list[dict]:
        return [{"job_id": "job-1"}]


class _AnalyticsService:
    def execution_summary(self) -> dict:
        return {
            "fill_rate": 0.0,
            "avg_slippage_bps": 0.0,
            "latency_ms_p50": 0.0,
            "latency_ms_p95": 0.0,
            "venue_score": 0.0,
            "as_of": "stale",
        }

    async def execution_summary_live(self) -> dict:
        return {
            "fill_rate": 0.82,
            "avg_slippage_bps": 1.7,
            "latency_ms_p50": 41.0,
            "latency_ms_p95": 88.0,
            "venue_score": 0.7844,
            "order_count": 7,
            "fill_count": 6,
            "as_of": "2026-03-22T00:00:02+00:00",
            "status": "ok",
        }


def _build_service() -> CommandCenterService:
    return CommandCenterService(
        v12_client=None,  # type: ignore[arg-type]
        dashboard_service=_DashboardService(),  # type: ignore[arg-type]
        portfolio_service=None,  # type: ignore[arg-type]
        risk_service=_RiskService(),  # type: ignore[arg-type]
        analytics_service=_AnalyticsService(),  # type: ignore[arg-type]
        monitoring_service=_MonitoringService(),  # type: ignore[arg-type]
        alert_service=_AlertService(),  # type: ignore[arg-type]
        scheduler_service=_SchedulerService(),  # type: ignore[arg-type]
        control_service=None,  # type: ignore[arg-type]
        analytics_repository=None,  # type: ignore[arg-type]
        audit_repository=None,  # type: ignore[arg-type]
        risk_repository=None,  # type: ignore[arg-type]
        notification_service=None,  # type: ignore[arg-type]
    )


def test_command_center_overview_prefers_live_execution_metrics() -> None:
    service = _build_service()
    payload = asyncio.run(service.get_overview())

    assert payload["fill_rate"] == 0.82
    assert payload["avg_slippage_bps"] == 1.7
    assert payload["execution_state"] == "executing"


def test_command_center_execution_latest_prefers_live_execution_metrics() -> None:
    service = _build_service()
    payload = asyncio.run(service.get_execution_latest())

    assert payload["order_count"] == 7
    assert payload["fill_count"] == 6
    assert payload["fill_rate"] == 0.82
    assert payload["latency_ms_p95"] == 88.0
    assert payload["venue_score"] == 0.7844
