from __future__ import annotations

import asyncio
import time

from app.core.deps import get_monitoring_service
from app.services.monitoring_service import MonitoringService


class _MonitoringRepository:
    def __init__(self, latest: dict | None = None) -> None:
        self._latest = latest
        self.inserted: list[dict] = []

    def latest_snapshot(self) -> dict | None:
        return self._latest

    def insert_snapshot(self, snapshot: dict) -> dict:
        self._latest = snapshot
        self.inserted.append(snapshot)
        return snapshot

    def latest_service_statuses(self) -> list[dict]:
        return []


class _ConcurrentV12Client:
    def __init__(self) -> None:
        self.planner_calls = 0
        self.state_calls = 0
        self.block_reason_calls = 0
        self.risk_budget_calls = 0

    async def _sleep(self) -> None:
        await asyncio.sleep(0.05)

    async def get_system_health(self) -> dict:
        await self._sleep()
        return {"status": "ok", "services": {"exchange": "connected"}, "as_of": "2026-03-22T00:00:00+00:00"}

    async def get_execution_quality(self) -> dict:
        await self._sleep()
        return {"status": "ok", "latency_ms_p50": 25.0, "latency_ms_p95": 40.0, "as_of": "2026-03-22T00:00:00+00:00"}

    async def get_runtime_status(self) -> dict:
        await self._sleep()
        return {"latest_run_timestamp": "2026-03-22T00:00:00+00:00", "as_of": "2026-03-22T00:00:00+00:00"}

    async def get_execution_planner_latest(self) -> dict:
        self.planner_calls += 1
        await self._sleep()
        return {"plan_count": 1, "latest_activity_at": "2026-03-22T00:00:00+00:00", "as_of": "2026-03-22T00:00:00+00:00"}

    async def get_execution_state_latest(self) -> dict:
        self.state_calls += 1
        await self._sleep()
        return {"execution_state": "running", "open_order_count": 1, "trading_state": "running", "as_of": "2026-03-22T00:00:00+00:00"}

    async def get_execution_block_reasons_latest(self) -> dict:
        self.block_reason_calls += 1
        await self._sleep()
        return {"items": []}

    async def get_risk_budget(self) -> dict:
        self.risk_budget_calls += 1
        await self._sleep()
        return {"trading_state": "running"}

    async def get_sprint5c_risk_latest(self) -> dict:
        await self._sleep()
        return {"trading_state": "running", "kill_switch": "normal", "alert_state": "ok"}


async def _get_system_returns_cached_snapshot_without_blocking() -> None:
    repo = _MonitoringRepository(
        latest={
            "system_status": "ok",
            "execution_status": "ok",
            "services": {"exchange": "connected"},
            "worker_status": "running",
            "as_of": "2000-01-01T00:00:00+00:00",
        }
    )
    service = MonitoringService(_ConcurrentV12Client(), repo)  # type: ignore[arg-type]

    payload = await service.get_system()

    assert payload["status"] == "ok"
    assert payload["dataStatus"] == "stale"
    assert payload["dataSource"] == "cache"
    assert payload["isStale"] is True
    assert repo.inserted == []

    assert service._background_refresh_task is not None
    await service._background_refresh_task

    assert len(repo.inserted) == 1
    assert repo.inserted[0]["system_status"] == "ok"


def test_get_system_returns_cached_snapshot_without_blocking_on_refresh() -> None:
    asyncio.run(_get_system_returns_cached_snapshot_without_blocking())


def test_refresh_parallelizes_upstream_reads() -> None:
    repo = _MonitoringRepository()
    service = MonitoringService(_ConcurrentV12Client(), repo)  # type: ignore[arg-type]

    started = time.perf_counter()
    payload = asyncio.run(service.refresh())
    elapsed = time.perf_counter() - started

    assert payload["system_status"] == "ok"
    assert payload["execution_status"] == "ok"
    assert payload["data_status"] == "ok"
    assert payload["data_source"] == "live"
    assert payload["is_stale"] is False
    assert elapsed < 0.2


def test_get_monitoring_service_is_shared_singleton() -> None:
    first = get_monitoring_service()
    second = get_monitoring_service()

    assert first is second


def test_refresh_summary_only_skips_execution_detail_reads() -> None:
    repo = _MonitoringRepository()
    client = _ConcurrentV12Client()
    service = MonitoringService(client, repo)  # type: ignore[arg-type]

    payload = asyncio.run(service.refresh(summary_only=True))

    assert payload["system_status"] == "ok"
    assert payload["execution_status"] == "ok"
    assert payload["data_status"] == "ok"
    assert client.planner_calls == 0
    assert client.state_calls == 0
    assert client.block_reason_calls == 0
    assert client.risk_budget_calls == 0
