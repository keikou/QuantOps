import pytest

from app.services.portfolio_truth_service import PortfolioTruthService


class DummyV12:
    async def get_portfolio_equity_latest(self):
        return {
            "total_equity": 110,
            "cash_balance": 100,
            "market_value": 10,
            "realized_pnl": 0,
            "unrealized_pnl": 10,
        }

    async def get_portfolio_positions_latest(self):
        return {
            "items": [
                {
                    "symbol": "BTC",
                    "signed_qty": 1,
                    "avg_entry_price": 100,
                    "mark_price": 110,
                    "unrealized_pnl": 10,
                }
            ]
        }


@pytest.mark.asyncio
async def test_portfolio_overview():
    svc = PortfolioTruthService(DummyV12())

    result = await svc.get_portfolio_overview()

    summary = result["summary"]

    assert summary["total_equity"] == 110
    assert summary["unrealized_pnl"] == 10
    assert summary["position_count"] == 1