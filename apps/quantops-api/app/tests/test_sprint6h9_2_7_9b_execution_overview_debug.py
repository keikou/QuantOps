from __future__ import annotations

import asyncio

from app.services.command_center_service import CommandCenterService
from app.services.dashboard_service import DashboardService


class _DashboardRepo:
    def list_jobs(self) -> list[dict]:
        return [{"job_id": "job-1", "status": "running"}]


class _AlertService:
    def list_alerts(self) -> dict:
        return {"items": [{"id": "a1"}], "open_count": 1}


class _DashboardV12Client:
    async def get_portfolio_positions(self) -> dict:
        return {
            "items": [
                {
                    "symbol": "BTCUSDT",
                    "signed_qty": 2.0,
                    "avg_price": 100.0,
                    "mark_price": 110.0,
                    "pnl": 20.0,
                    "weight": 0.4,
                },
                {
                    "symbol": "ETHUSDT",
                    "signed_qty": -1.0,
                    "avg_price": 50.0,
                    "mark_price": 40.0,
                    "pnl": -10.0,
                    "weight": -0.2,
                    "side": "short",
                },
            ],
            "as_of": "2026-03-22T00:00:00+00:00",
        }

    async def get_portfolio_dashboard(self) -> dict:
        return {
            "summary": {
                "cash_balance": 1000.0,
                "realized_pnl": 5.0,
                "unrealized_pnl": 0.0,
                "gross_exposure": 0.0,
                "net_exposure": 0.0,
            },
            "as_of": "2026-03-22T00:00:00+00:00",
        }

    async def get_runtime_status(self) -> dict:
        return {"latest_run_id": "run-1", "as_of": "2026-03-22T00:00:01+00:00"}

    async def get_strategy_registry(self) -> dict:
        return {"enabled_count": 2, "strategies": [{"strategy_id": "s1"}, {"strategy_id": "s2"}]}


def test_dashboard_overview_debug_reports_derived_financial_field_sources() -> None:
    service = DashboardService(_DashboardV12Client(), _DashboardRepo(), _AlertService())  # type: ignore[arg-type]

    payload = asyncio.run(service.get_overview_debug())

    assert payload["scope"] == "dashboard.overview"
    assert payload["summary"]["total_equity"] == 1180.0
    assert payload["summary"]["used_margin"] == 250.0
    assert payload["summary"]["unrealized"] == 10.0
    assert payload["summary"]["gross_exposure"] == 0.6
    assert payload["summary"]["net_exposure"] == 0.2
    assert payload["provenance"]["field_sources"]["used_margin"] == "derived(sum(abs(position.signed_qty) * position.avg_price))"
    assert payload["provenance"]["field_sources"]["free_margin"] == "derived(total_equity - used_margin)"
    assert payload["provenance"]["field_sources"]["gross_exposure"] == "derived(sum(abs(position.weight)))"
    assert payload["provenance"]["field_sources"]["net_exposure"] == "derived(sum(position.weight))"


class _CommandCenterDashboardService:
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


class _SchedulerService:
    def list_jobs(self) -> list[dict]:
        return [{"job_id": "job-1"}]


class _ExecutionAnalyticsService:
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
            "as_of": "2026-03-22T00:00:02+00:00",
            "status": "ok",
        }

    async def latest_execution_planner(self) -> dict:
        return {"plan_count": 4, "trading_state": "running", "as_of": "2026-03-22T00:00:02+00:00"}


class _ExecutionV12Client:
    async def get_execution_state_latest(self) -> dict:
        return {
            "execution_state": "partially_filled",
            "reason": "recent_fill_detected",
            "open_order_count": 7,
            "as_of": "2026-03-22T00:00:02+00:00",
        }

    async def get_execution_orders(self, limit: int | None = None) -> dict:
        return {"items": [{"order_id": "o1"}, {"order_id": "o2"}], "as_of": "2026-03-22T00:00:02+00:00"}

    async def get_execution_fills(self, limit: int | None = None) -> dict:
        return {"items": [{"fill_id": "f1"}], "as_of": "2026-03-22T00:00:02+00:00"}


def test_command_center_execution_debug_reports_live_bridge_when_stored_summary_is_empty() -> None:
    service = CommandCenterService(
        v12_client=_ExecutionV12Client(),  # type: ignore[arg-type]
        dashboard_service=_CommandCenterDashboardService(),  # type: ignore[arg-type]
        portfolio_service=None,  # type: ignore[arg-type]
        risk_service=_RiskService(),  # type: ignore[arg-type]
        analytics_service=_ExecutionAnalyticsService(),  # type: ignore[arg-type]
        monitoring_service=_MonitoringService(),  # type: ignore[arg-type]
        alert_service=_AlertService(),  # type: ignore[arg-type]
        scheduler_service=_SchedulerService(),  # type: ignore[arg-type]
        control_service=None,  # type: ignore[arg-type]
        analytics_repository=None,  # type: ignore[arg-type]
        audit_repository=None,  # type: ignore[arg-type]
        risk_repository=None,  # type: ignore[arg-type]
        notification_service=None,  # type: ignore[arg-type]
    )

    payload = asyncio.run(service.get_execution_debug())

    assert payload["scope"] == "command_center.execution"
    assert payload["status"] == "ok"
    assert payload["source"] == "live"
    assert payload["reason"] == "stored_summary_empty"
    assert payload["provenance"]["read_mode"] == "live_bridge"
    assert payload["summary"]["order_count"] == 2
    assert payload["summary"]["fill_count"] == 1
    assert payload["summary"]["execution_state"] == "partially_filled"
    assert payload["counts"]["active_plans"] == 4
    assert payload["counts"]["open_orders"] == 7
    assert payload["counts"]["fills_considered"] == 1
