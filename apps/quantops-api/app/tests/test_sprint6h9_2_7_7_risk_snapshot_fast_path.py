from __future__ import annotations

import asyncio
import time

from app.services.risk_service import RiskService


class _RiskRepository:
    def __init__(self, latest: dict | None = None) -> None:
        self._latest = latest
        self.inserted: list[dict] = []

    def latest_snapshot(self) -> dict | None:
        return self._latest

    def insert_snapshot(self, snapshot: dict) -> dict:
        self._latest = snapshot
        self.inserted.append(snapshot)
        return snapshot

    def get_trading_state(self) -> dict:
        return {"trading_state": "running"}


class _ConcurrentV12Client:
    async def _sleep(self) -> None:
        await asyncio.sleep(0.05)

    async def get_risk_budget(self) -> dict:
        await self._sleep()
        return {"risk": {"per_strategy": [{"budget_usage": 0.9}]}, "global": {"status": "ok", "alerts": []}, "as_of": "2026-03-22T00:00:00+00:00"}

    async def get_execution_quality(self) -> dict:
        await self._sleep()
        return {"fill_rate": 1.0, "avg_slippage_bps": 1.2, "as_of": "2026-03-22T00:00:00+00:00"}

    async def get_portfolio_diagnostics(self) -> dict:
        await self._sleep()
        return {"diagnostics": {"kept_signals": 3}}

    async def get_portfolio_positions(self) -> dict:
        await self._sleep()
        return {"items": [{"weight": 0.4}, {"weight": -0.2}], "as_of": "2026-03-22T00:00:00+00:00"}

    async def get_portfolio_dashboard(self) -> dict:
        await self._sleep()
        return {"summary": {"margin_utilization": 0.6, "collateral_equity": 1000.0, "available_margin": 400.0}}


async def _get_stale_snapshot_returns_cached_data_and_refreshes_in_background() -> None:
    repo = _RiskRepository(
        latest={
            "gross_exposure": 0.5,
            "net_exposure": 0.1,
            "leverage": 0.5,
            "drawdown": 0.0,
            "var_95": 0.04,
            "risk_limit": {},
            "alert_state": "ok",
            "trading_state": "running",
            "as_of": "2000-01-01T00:00:00+00:00",
        }
    )
    service = RiskService(_ConcurrentV12Client(), repo)  # type: ignore[arg-type]

    payload = await service.get_snapshot()

    assert payload["gross_exposure"] == 0.5
    assert payload["data_status"] == "stale"
    assert payload["data_source"] == "cache"
    assert payload["is_stale"] is True
    assert repo.inserted == []

    assert service._background_refresh_task is not None
    await service._background_refresh_task

    assert len(repo.inserted) == 1
    assert repo.inserted[0]["gross_exposure"] == 0.6


def test_get_snapshot_returns_cached_snapshot_without_blocking_on_rebuild() -> None:
    asyncio.run(_get_stale_snapshot_returns_cached_data_and_refreshes_in_background())


def test_build_snapshot_parallelizes_upstream_calls() -> None:
    repo = _RiskRepository()
    service = RiskService(_ConcurrentV12Client(), repo)  # type: ignore[arg-type]

    started = time.perf_counter()
    payload = asyncio.run(service.build_snapshot())
    elapsed = time.perf_counter() - started

    assert payload["gross_exposure"] == 0.6
    assert payload["net_exposure"] == 0.2
    assert payload["alert_state"] == "ok"
    assert "data_status" not in payload
    assert "data_source" not in payload
    assert "is_stale" not in payload
    assert elapsed < 0.15
