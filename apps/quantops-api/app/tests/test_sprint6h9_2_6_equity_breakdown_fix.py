from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from app.services.dashboard_service import DashboardService
from app.services.equity_breakdown import compute_equity_breakdown
from app.services.portfolio_service import PortfolioService


class _Repo:
    def list_jobs(self):
        return []


class _AlertService:
    def evaluate_rules(self) -> None:
        return None

    def list_alerts(self) -> dict:
        return {'items': [], 'open_count': 0}


@pytest.mark.parametrize(
    ('row', 'expected_used'),
    [
        ({'quantity': 2, 'avg_price': 100, 'pnl': 5}, 200.0),
        ({'qty': 3, 'avg_entry_price': 10, 'unrealized_pnl': -1}, 30.0),
        ({'position_qty': 4, 'avg': 7.5, 'unrealized': 2}, 30.0),
        ({'quantity': None, 'avg_price': None, 'pnl': None}, 0.0),
    ],
)
def test_compute_equity_breakdown_accepts_multiple_price_keys(row: dict, expected_used: float) -> None:
    payload = compute_equity_breakdown(
        {'summary': {'balance': 1000.0}},
        {'items': [row]},
    )
    assert payload['used_margin'] == round(expected_used, 2)


@pytest.mark.asyncio
async def test_dashboard_service_survives_equity_breakdown_failure() -> None:
    client = AsyncMock()
    client.get_portfolio_positions.return_value = {'items': []}
    client.get_portfolio_dashboard.return_value = {'summary': {'total_equity': 1234.56, 'cash_balance': 1000.0, 'used_margin': 200.0, 'unrealized_pnl': 34.56}}
    client.get_execution_quality.return_value = {'as_of': '2026-03-20T00:00:00+00:00'}
    client.get_risk_budget.return_value = {'risk': {}}
    client.get_runtime_status.return_value = {'as_of': '2026-03-20T00:00:00+00:00'}
    client.get_shadow_summary.return_value = {}
    client.get_strategy_registry.return_value = {'strategies': []}

    service = DashboardService(client, _Repo(), _AlertService())
    with patch('app.services.dashboard_service.compute_equity_breakdown', side_effect=RuntimeError('boom')):
        overview = await service.get_overview()

    assert overview['total_equity'] == 1234.56
    assert overview['balance'] == 1000.0
    assert overview['free_margin'] == 1034.56
    assert overview['used_margin'] == 200.0
    assert overview['unrealized'] == 34.56


@pytest.mark.asyncio
async def test_portfolio_service_survives_equity_breakdown_failure() -> None:
    client = AsyncMock()
    client.get_portfolio_dashboard.return_value = {'summary': {'total_equity': 9876.54, 'cash_balance': 9000.0, 'used_margin': 700.0, 'unrealized_pnl': 176.54}}
    client.get_portfolio_positions.return_value = {'items': []}
    client.get_execution_quality.return_value = {'fill_rate': 0.0}
    client.get_equity_history.return_value = {'items': []}

    service = PortfolioService(client)
    with patch.object(service, 'get_positions', AsyncMock(return_value=[])):
        with patch('app.services.portfolio_service.compute_equity_breakdown', side_effect=RuntimeError('boom')):
            overview = await service.get_overview()

    assert overview['total_equity'] == 9876.54
    assert overview['balance'] == 9000.0
    assert overview['free_margin'] == 9176.54
    assert overview['used_margin'] == 700.0
    assert overview['unrealized'] == 176.54
