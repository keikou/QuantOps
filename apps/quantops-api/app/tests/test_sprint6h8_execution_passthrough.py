import asyncio

from app.clients.v12_client import V12Client
from app.services.execution_service import ExecutionService


async def _main():
    client = V12Client(base_url='http://localhost:8000', mock_mode=True)
    service = ExecutionService(client)
    view = await service.get_view_latest()
    planner = await service.get_planner_latest()
    orders = await service.get_orders()
    fills = await service.get_fills()
    state = await service.get_state_latest()
    reasons = await service.get_block_reasons_latest()

    assert view['status'] == 'ok'
    assert view['planner']['status'] == 'ok'
    assert view['state']['status'] == 'ok'
    assert planner['status'] == 'ok'
    assert 'items' in orders
    assert 'items' in fills
    assert state['status'] == 'ok'
    assert 'execution_state' in state
    assert reasons['status'] == 'ok'
    assert isinstance(reasons['items'], list)


def test_execution_service_passthrough_endpoints():
    asyncio.run(_main())


class _OldSnapshotExecutionClient:
    async def get_execution_view_latest(self) -> dict:
        return {}

    async def get_execution_planner_latest(self) -> dict:
        return {
            "status": "ok",
            "as_of": "2026-03-24T19:31:01+00:00",
            "items": [{"plan_id": "plan-1"}],
        }

    async def get_execution_state_latest(self) -> dict:
        return {
            "status": "ok",
            "as_of": "2026-03-24T19:31:01+00:00",
            "execution_state": "running",
        }

    async def get_execution_orders(self, limit: int = 100) -> dict:
        return {
            "status": "ok",
            "as_of": "2026-03-24T19:31:01+00:00",
            "items": [
                {"order_id": "order-1", "symbol": "BTCUSDT", "status": "filled", "updated_at": "2026-03-24T19:31:01+00:00"},
            ],
        }

    async def get_execution_fills(self, limit: int = 100) -> dict:
        return {
            "status": "ok",
            "as_of": "2026-03-24T19:31:01+00:00",
            "items": [
                {"fill_id": "fill-1", "symbol": "BTCUSDT", "status": "filled", "created_at": "2026-03-24T19:31:01+00:00"},
            ],
        }


async def _cache_main():
    service = ExecutionService(_OldSnapshotExecutionClient())  # type: ignore[arg-type]
    first_view = await service.get_view_latest()
    second_view = await service.get_view_latest()
    first_planner = await service.get_planner_latest()
    second_planner = await service.get_planner_latest()
    first_state = await service.get_state_latest()
    second_state = await service.get_state_latest()
    first_orders = await service.get_orders(limit=10)
    second_orders = await service.get_orders(limit=10)
    first_fills = await service.get_fills(limit=10)
    second_fills = await service.get_fills(limit=10)
    assert first_view["build_status"] == "live"
    assert second_view["build_status"] == "fresh_cache"
    assert first_view["planner"]["status"] == "ok"
    assert first_view["state"]["status"] == "ok"
    assert first_planner["build_status"] == "live"
    assert second_planner["build_status"] == "fresh_cache"
    assert first_state["build_status"] == "live"
    assert second_state["build_status"] == "fresh_cache"
    assert first_orders["build_status"] == "live"
    assert second_orders["build_status"] == "fresh_cache"
    assert first_fills["build_status"] == "live"
    assert second_fills["build_status"] == "fresh_cache"


def test_execution_service_feed_cache_uses_cached_at_not_source_snapshot_age():
    asyncio.run(_cache_main())
