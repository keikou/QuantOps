from __future__ import annotations

import asyncio

from app.services.portfolio_service import PortfolioService


class _PortfolioV12Client:
    async def get_portfolio_dashboard(self) -> dict:
        return {
            "summary": {
                "cash_balance": 50000.0,
                "gross_exposure": 0.0,
                "net_exposure": 0.0,
                "long_exposure": 0.0,
                "short_exposure": 0.0,
                "realized_pnl": 0.0,
                "unrealized_pnl": 0.0,
            },
            "quotes_as_of": "2026-03-22T00:00:00+00:00",
            "as_of": "2026-03-22T00:00:00+00:00",
        }

    async def get_portfolio_positions(self) -> dict:
        return {
            "items": [
                {
                    "symbol": "BTCUSDT",
                    "side": "long",
                    "signed_qty": 2.0,
                    "quantity": 2.0,
                    "avg_price": 10000.0,
                    "mark_price": 11000.0,
                    "pnl": 2000.0,
                    "weight": 0.4,
                    "strategy_id": "s1",
                },
                {
                    "symbol": "ETHUSDT",
                    "side": "short",
                    "signed_qty": -1.0,
                    "quantity": -1.0,
                    "avg_entry_price": 5000.0,
                    "markPrice": 4500.0,
                    "unrealized_pnl": 500.0,
                    "target_weight": 0.2,
                    "run_id": "run-2",
                    "stale": True,
                },
            ],
            "as_of": "2026-03-22T00:00:00+00:00",
        }

    async def get_execution_quality(self) -> dict:
        return {"fill_rate": 0.9}

    async def get_equity_history(self) -> dict:
        return {
            "items": [
                {"value": 100000.0},
                {"value": 101000.0},
                {"value": 100500.0},
            ]
        }


def test_portfolio_positions_debug_reports_normalized_truth_sources() -> None:
    service = PortfolioService(_PortfolioV12Client())  # type: ignore[arg-type]

    payload = asyncio.run(service.get_positions_debug())

    assert payload["scope"] == "portfolio.positions"
    assert payload["status"] == "ok"
    assert payload["summary"]["position_count"] == 2
    assert payload["summary"]["stale_positions"] == 1
    assert payload["counts"]["stale_positions"] == 1
    assert payload["provenance"]["read_mode"] == "normalized_positions"
    assert payload["provenance"]["field_sources"][0]["sources"]["mark_price"] == "mark_price|markPrice|price|last_price"


def test_portfolio_overview_debug_reports_equity_trace_and_derived_fields() -> None:
    service = PortfolioService(_PortfolioV12Client())  # type: ignore[arg-type]

    payload = asyncio.run(service.get_overview_debug())

    assert payload["scope"] == "portfolio.overview"
    assert payload["status"] == "ok"
    assert payload["summary"]["total_equity"] == 67500.0
    assert payload["summary"]["used_margin"] == 25000.0
    assert payload["summary"]["free_margin"] == 42500.0
    assert payload["summary"]["unrealized"] == 2500.0
    assert payload["summary"]["gross_exposure"] == 0.6
    assert payload["summary"]["net_exposure"] == 0.2
    assert payload["provenance"]["field_sources"]["total_equity"] == "derived(balance + market_value)"
    assert payload["provenance"]["field_sources"]["used_margin"] == "derived(sum(abs(position.quantity) * position.avg_price))"
    assert payload["provenance"]["equity_trace"]["formula"] == "total_equity = balance + market_value"
    assert payload["counts"]["position_count"] == 2
    assert payload["counts"]["stale_positions"] == 1
