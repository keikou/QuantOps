import asyncio

from app.clients.v12_client import V12Client
from app.services.execution_service import ExecutionService


async def _main():
    client = V12Client(base_url='http://localhost:8000', mock_mode=True)
    service = ExecutionService(client)
    planner = await service.get_planner_latest()
    orders = await service.get_orders()
    fills = await service.get_fills()
    state = await service.get_state_latest()
    reasons = await service.get_block_reasons_latest()

    assert planner['status'] == 'ok'
    assert 'items' in orders
    assert 'items' in fills
    assert state['status'] == 'ok'
    assert 'execution_state' in state
    assert reasons['status'] == 'ok'
    assert isinstance(reasons['items'], list)


def test_execution_service_passthrough_endpoints():
    asyncio.run(_main())
