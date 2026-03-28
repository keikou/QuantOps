from __future__ import annotations

import asyncio
import time

from app.core.deps import get_portfolio_service
from app.services.portfolio_service import PortfolioService


class _V12Client:
    def __init__(self) -> None:
        self.overview_calls = 0
        self.positions_calls = 0

    async def get_portfolio_dashboard(self) -> dict:
        self.overview_calls += 1
        await asyncio.sleep(0.05)
        return {
            "summary": {
                "total_equity": 1000.0,
                "cash_balance": 400.0,
                "free_cash": 350.0,
                "used_margin": 650.0,
                "gross_exposure": 0.6,
                "net_exposure": 0.2,
                "realized_pnl": 10.0,
                "unrealized_pnl": 20.0,
                "fees_paid": 1.0,
                "drawdown": 0.03,
                "margin_utilization": 0.6,
                "as_of": "2026-03-25T00:00:00+00:00",
            },
            "positions": [
                {
                    "symbol": "BTCUSDT",
                    "side": "long",
                    "signed_qty": 0.1,
                    "abs_qty": 0.1,
                    "avg_entry_price": 50000.0,
                    "mark_price": 51000.0,
                    "unrealized_pnl": 20.0,
                    "exposure_notional": 200.0,
                    "strategy_id": "trend_core",
                    "alpha_family": "trend",
                    "stale": False,
                }
            ],
            "as_of": "2026-03-25T00:00:00+00:00",
            "source_snapshot_time": "2026-03-25T00:00:00+00:00",
            "build_status": "live",
        }

    async def get_portfolio_positions(self) -> dict:
        self.positions_calls += 1
        await asyncio.sleep(0.05)
        return {
            "items": [
                {
                    "symbol": "BTCUSDT",
                    "side": "long",
                    "quantity": 0.1,
                    "avg_price": 50000.0,
                    "mark_price": 51000.0,
                    "pnl": 20.0,
                    "weight": 0.2,
                    "strategy_id": "trend_core",
                    "alpha_family": "trend",
                }
            ],
            "as_of": "2026-03-25T00:00:00+00:00",
            "source_snapshot_time": "2026-03-25T00:00:00+00:00",
            "build_status": "live",
        }


def test_get_portfolio_service_is_shared_singleton() -> None:
    first = get_portfolio_service()
    second = get_portfolio_service()
    assert first is second


def test_get_overview_parallelizes_and_caches() -> None:
    client = _V12Client()
    service = PortfolioService(client)  # type: ignore[arg-type]

    async def run_test():
        first, second = await asyncio.gather(service.get_overview(), service.get_overview())
        third = await service.get_overview()
        return first, second, third

    started = time.perf_counter()
    first, second, third = asyncio.run(run_test())
    elapsed = time.perf_counter() - started

    assert first["total_equity"] == 1000.0
    assert second["gross_exposure"] == 0.6
    assert third["build_status"] == "fresh_cache"
    assert client.overview_calls == 1
    assert client.positions_calls == 1
    assert elapsed < 0.2


def test_get_overview_ignores_stale_inflight_and_rebuilds() -> None:
    client = _V12Client()
    service = PortfolioService(client)  # type: ignore[arg-type]

    async def run_test() -> dict:
        stale_task = asyncio.create_task(asyncio.sleep(30))
        service._overview_inflight_task = stale_task
        service._overview_inflight_started_at = time.perf_counter() - 30.0
        try:
            return await service.get_overview()
        finally:
            stale_task.cancel()
            try:
                await stale_task
            except asyncio.CancelledError:
                pass

    payload = asyncio.run(run_test())

    assert payload["total_equity"] == 1000.0
    assert payload["used_margin"] == 5000.0
    assert payload["free_margin"] == -4000.0
    assert client.overview_calls == 1
    assert client.positions_calls == 1
