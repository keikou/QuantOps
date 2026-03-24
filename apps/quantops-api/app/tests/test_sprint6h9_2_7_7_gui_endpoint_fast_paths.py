from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
import time

from app.core.deps import get_dashboard_service, get_portfolio_service
from app.services.dashboard_service import DashboardService
from app.services.portfolio_service import PortfolioService


class _SchedulerRepository:
    def list_jobs(self) -> list[dict]:
        return [{"status": "running"}]


class _AlertService:
    def list_alerts(self) -> dict:
        return {"items": [], "open_count": 0}


class _DashboardClient:
    async def _sleep(self) -> None:
        await asyncio.sleep(0.05)

    async def get_portfolio_positions(self) -> dict:
        await self._sleep()
        return {
            "items": [
                {"symbol": "BTCUSDT", "weight": 0.4, "pnl": 10.0},
                {"symbol": "ETHUSDT", "weight": -0.2, "side": "short", "pnl": -2.0},
            ],
            "as_of": "2026-03-22T00:00:00+00:00",
        }

    async def get_portfolio_dashboard(self) -> dict:
        await self._sleep()
        return {
            "summary": {
                "total_equity": 100.0,
                "cash_balance": 30.0,
                "used_margin": 70.0,
                "free_margin": 30.0,
                "unrealized_pnl": 8.0,
                "gross_exposure": 0.6,
                "net_exposure": 0.2,
            },
            "as_of": "2026-03-22T00:00:00+00:00",
        }

    async def get_runtime_status(self) -> dict:
        await self._sleep()
        return {"mock_mode": False, "latest_run_id": "run-1", "as_of": "2026-03-22T00:00:00+00:00"}

    async def get_strategy_registry(self) -> dict:
        await self._sleep()
        return {"enabled_count": 2}


class _SlowDashboardClient(_DashboardClient):
    async def get_portfolio_positions(self) -> dict:
        await asyncio.sleep(0.3)
        return await super().get_portfolio_positions()

    async def get_runtime_status(self) -> dict:
        await asyncio.sleep(0.3)
        return await super().get_runtime_status()

    async def get_strategy_registry(self) -> dict:
        await asyncio.sleep(0.3)
        return await super().get_strategy_registry()


class _PortfolioClient:
    def __init__(self) -> None:
        self.execution_quality_calls = 0
        self.equity_history_calls = 0

    async def _sleep(self) -> None:
        await asyncio.sleep(0.05)

    async def get_portfolio_dashboard(self) -> dict:
        await self._sleep()
        return {
            "summary": {
                "total_equity": 100.0,
                "cash_balance": 30.0,
                "used_margin": 70.0,
                "free_margin": 30.0,
                "unrealized_pnl": 8.0,
                "gross_exposure": 0.6,
                "net_exposure": 0.2,
            },
            "positions": [
                {"symbol": "BTCUSDT", "weight": 0.4, "pnl": 10.0},
                {"symbol": "ETHUSDT", "weight": 0.2, "side": "short", "pnl": -2.0},
            ],
            "as_of": "2026-03-22T00:00:00+00:00",
        }

    async def get_portfolio_positions(self) -> dict:
        await self._sleep()
        return {
            "items": [
                {"symbol": "BTCUSDT", "weight": 0.4, "pnl": 10.0},
                {"symbol": "ETHUSDT", "weight": 0.2, "side": "short", "pnl": -2.0},
            ],
            "as_of": "2026-03-22T00:00:00+00:00",
        }

    async def get_execution_quality(self, *, live: bool = False) -> dict:
        self.execution_quality_calls += 1
        await self._sleep()
        return {"fill_rate": 1.0}

    async def get_equity_history(self, *, limit: int | None = None, live: bool = False) -> dict:
        self.equity_history_calls += 1
        await self._sleep()
        return {"items": [{"value": 100.0}, {"value": 101.0}, {"value": 102.0}], "limit": limit, "live": live}


class _CountingDashboardService(DashboardService):
    def __init__(self) -> None:
        super().__init__(_DashboardClient(), _SchedulerRepository(), _AlertService())  # type: ignore[arg-type]
        self.build_calls = 0

    async def _build_overview_live(self) -> dict:
        self.build_calls += 1
        await asyncio.sleep(0.05)
        return {
            "total_equity": 100.0,
            "active_strategies": 2,
            "open_alerts": 0,
            "latest_run_id": "run-1",
            "as_of": "2026-03-22T00:00:00+00:00",
        }


def test_dashboard_overview_parallelizes_upstream_reads() -> None:
    service = DashboardService(_DashboardClient(), _SchedulerRepository(), _AlertService())  # type: ignore[arg-type]

    started = time.perf_counter()
    payload = asyncio.run(service.get_overview())
    elapsed = time.perf_counter() - started

    assert payload["total_equity"] == 100.0
    assert payload["active_strategies"] == 2
    assert payload["build_status"] == "live"
    assert payload["source_snapshot_time"] == "2026-03-22T00:00:00+00:00"
    assert elapsed < 0.15


def test_dashboard_overview_bounded_fast_path_returns_primary_truth_when_aux_calls_are_slow() -> None:
    service = DashboardService(_SlowDashboardClient(), _SchedulerRepository(), _AlertService())  # type: ignore[arg-type]
    service.OVERVIEW_PRIMARY_TIMEOUT_SECONDS = 0.12
    service.OVERVIEW_AUX_TIMEOUT_SECONDS = 0.08

    started = time.perf_counter()
    payload = asyncio.run(service.get_overview())
    elapsed = time.perf_counter() - started

    assert payload["total_equity"] == 100.0
    assert payload["active_strategies"] == 0
    assert payload["latest_run_id"] is None
    assert payload["build_status"] == "live"
    assert elapsed < 0.2


def test_portfolio_positions_skips_unused_execution_quality_call() -> None:
    client = _PortfolioClient()
    service = PortfolioService(client)  # type: ignore[arg-type]

    payload = asyncio.run(service.get_positions())

    assert len(payload) == 2
    assert client.execution_quality_calls == 0


def test_portfolio_overview_parallelizes_upstream_reads() -> None:
    client = _PortfolioClient()
    service = PortfolioService(client)  # type: ignore[arg-type]

    started = time.perf_counter()
    payload = asyncio.run(service.get_overview())
    elapsed = time.perf_counter() - started

    assert payload["total_equity"] == 100.0
    assert "fill_rate" not in payload
    assert elapsed < 0.1


def test_portfolio_metrics_parallelizes_upstream_reads() -> None:
    client = _PortfolioClient()
    service = PortfolioService(client)  # type: ignore[arg-type]

    started = time.perf_counter()
    payload = asyncio.run(service.get_metrics())
    elapsed = time.perf_counter() - started

    assert payload["fill_rate"] == 1.0
    assert elapsed < 0.15


def test_portfolio_metrics_uses_short_ttl_cache_and_coalesces() -> None:
    client = _PortfolioClient()
    service = PortfolioService(client)  # type: ignore[arg-type]

    async def run_test() -> tuple[dict, dict, dict]:
        first, second = await asyncio.gather(service.get_metrics(), service.get_metrics())
        third = await service.get_metrics()
        return first, second, third

    first, second, third = asyncio.run(run_test())

    assert first["fill_rate"] == 1.0
    assert second["expected_sharpe"] == first["expected_sharpe"]
    assert third["fill_rate"] == 1.0
    assert client.execution_quality_calls == 1
    assert client.equity_history_calls == 1


def test_portfolio_metrics_returns_stale_cache_and_refreshes_in_background() -> None:
    client = _PortfolioClient()
    service = PortfolioService(client)  # type: ignore[arg-type]
    stale_payload = {"fill_rate": 0.4, "expected_sharpe": 0.2, "expected_volatility": 0.1, "as_of": "2026-03-22T00:00:00+00:00"}
    service._metrics_cache = dict(stale_payload)
    service._metrics_cache_updated_at = datetime.now(timezone.utc)
    service._metrics_cache_expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)

    async def run_test() -> dict:
        payload = await service.get_metrics()
        await asyncio.sleep(0.12)
        return payload

    payload = asyncio.run(run_test())

    assert payload == stale_payload
    assert client.execution_quality_calls == 1
    assert client.equity_history_calls == 1
    assert service._metrics_cache is not None
    assert service._metrics_cache["fill_rate"] == 1.0


def test_get_portfolio_service_is_shared_singleton() -> None:
    first = get_portfolio_service()
    second = get_portfolio_service()

    assert first is second


def test_dashboard_overview_coalesces_concurrent_live_builds() -> None:
    service = _CountingDashboardService()

    async def run_test() -> tuple[dict, dict]:
        return await asyncio.gather(service.get_overview(), service.get_overview())

    first, second = asyncio.run(run_test())

    assert first["total_equity"] == 100.0
    assert second["latest_run_id"] == "run-1"
    assert service.build_calls == 1


def test_dashboard_overview_returns_stale_cache_and_refreshes_in_background() -> None:
    service = _CountingDashboardService()
    stale_payload = {
        "total_equity": 90.0,
        "active_strategies": 1,
        "open_alerts": 0,
        "latest_run_id": "run-stale",
        "as_of": "2026-03-22T00:00:00+00:00",
    }
    service._overview_cache = dict(stale_payload)

    async def run_test() -> dict:
        payload = await service.get_overview()
        await asyncio.sleep(0.12)
        return payload

    payload = asyncio.run(run_test())

    assert payload["total_equity"] == stale_payload["total_equity"]
    assert payload["latest_run_id"] == stale_payload["latest_run_id"]
    assert payload["build_status"] == "stale_cache"
    assert service.build_calls == 1
    assert service._overview_cache is not None
    assert service._overview_cache["latest_run_id"] == "run-1"


def test_dashboard_overview_marks_stale_and_fresh_cache_responses() -> None:
    service = _CountingDashboardService()
    service._overview_cache = {
        "total_equity": 90.0,
        "active_strategies": 1,
        "open_alerts": 0,
        "latest_run_id": "run-stale",
        "as_of": "2026-03-22T00:00:00+00:00",
        "source_snapshot_time": "2026-03-22T00:00:00+00:00",
    }

    stale_payload = asyncio.run(service.get_overview())
    assert stale_payload["build_status"] == "stale_cache"

    service._overview_cache = {
        "total_equity": 91.0,
        "active_strategies": 1,
        "open_alerts": 0,
        "latest_run_id": "run-fresh",
        "as_of": datetime.now(timezone.utc).isoformat(),
        "source_snapshot_time": datetime.now(timezone.utc).isoformat(),
    }

    fresh_payload = asyncio.run(service.get_overview())
    assert fresh_payload["build_status"] == "fresh_cache"
    assert fresh_payload["data_freshness_sec"] is not None


def test_get_dashboard_service_is_shared_singleton() -> None:
    first = get_dashboard_service()
    second = get_dashboard_service()

    assert first is second
