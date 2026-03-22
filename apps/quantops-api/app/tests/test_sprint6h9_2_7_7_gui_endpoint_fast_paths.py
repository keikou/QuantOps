from __future__ import annotations

import asyncio
import time

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


class _PortfolioClient:
    def __init__(self) -> None:
        self.execution_quality_calls = 0

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

    async def get_execution_quality(self) -> dict:
        self.execution_quality_calls += 1
        await self._sleep()
        return {"fill_rate": 1.0}

    async def get_equity_history(self) -> dict:
        await self._sleep()
        return {"items": [{"value": 100.0}, {"value": 101.0}, {"value": 102.0}]}


def test_dashboard_overview_parallelizes_upstream_reads() -> None:
    service = DashboardService(_DashboardClient(), _SchedulerRepository(), _AlertService())  # type: ignore[arg-type]

    started = time.perf_counter()
    payload = asyncio.run(service.get_overview())
    elapsed = time.perf_counter() - started

    assert payload["total_equity"] == 100.0
    assert payload["active_strategies"] == 2
    assert elapsed < 0.15


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
    assert payload["fill_rate"] == 1.0
    assert elapsed < 0.15
