import asyncio

from app.clients.v12_client import V12Client
from app.services.dashboard_service import DashboardService


class _Repo:
    def list_jobs(self):
        return []


async def _main():
    client = V12Client(base_url='http://localhost:8000', mock_mode=False)

    async def degraded(*args, **kwargs):
        return {'status': 'degraded', 'items': [], 'positions': [], 'strategies': [], 'alerts': [], 'risk': {}, 'global': {}}

    client.get_portfolio_positions = degraded
    client.get_execution_quality = degraded
    client.get_risk_budget = degraded
    client.get_runtime_status = degraded
    client.get_shadow_summary = degraded
    client.get_strategy_registry = degraded

    service = DashboardService(client, _Repo())
    overview = await service.get_overview()
    assert overview['portfolio_value'] == 0.0
    assert overview['gross_exposure'] == 0.0
    assert overview['alerts'] == []


def test_dashboard_handles_degraded_upstream_payloads():
    asyncio.run(_main())
