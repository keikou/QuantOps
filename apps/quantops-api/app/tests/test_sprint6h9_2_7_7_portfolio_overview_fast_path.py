from __future__ import annotations

import asyncio
import time

from app.core.deps import get_portfolio_service
from app.services.portfolio_service import PortfolioService


class _V12Client:
    def __init__(self) -> None:
        self.overview_calls = 0

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
    assert third["build_status"] == "live"
    assert client.overview_calls == 1
    assert elapsed < 0.2
