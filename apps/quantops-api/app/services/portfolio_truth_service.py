from __future__ import annotations

from typing import Any

from app.clients.v12_client import V12Client


class PortfolioTruthService:
    def __init__(self, v12_client: V12Client) -> None:
        self.v12_client = v12_client

    async def get_portfolio_overview(self) -> dict[str, Any]:
        summary = await self._get_v12_equity_latest()
        positions_payload = await self._get_v12_positions_latest()
        positions = positions_payload.get("items", positions_payload.get("positions", []))

        total_equity = float(summary.get("total_equity", 0.0) or 0.0)
        cash_balance = float(summary.get("cash_balance", 0.0) or 0.0)
        market_value = float(summary.get("market_value", 0.0) or 0.0)
        realized_pnl = float(summary.get("realized_pnl", 0.0) or 0.0)
        unrealized_pnl = float(summary.get("unrealized_pnl", 0.0) or 0.0)

        long_exposure = float(summary.get("long_exposure", 0.0) or 0.0)
        short_exposure = float(summary.get("short_exposure", 0.0) or 0.0)
        gross_exposure = summary.get("gross_exposure")
        if gross_exposure is None:
            gross_exposure = long_exposure + short_exposure

        net_exposure = summary.get("net_exposure")
        if net_exposure is None:
            net_exposure = market_value

        return {
            "status": "ok",
            "summary": {
                "total_equity": total_equity,
                "cash_balance": cash_balance,
                "market_value": market_value,
                "gross_exposure": float(gross_exposure or 0.0),
                "net_exposure": float(net_exposure or 0.0),
                "long_exposure": long_exposure,
                "short_exposure": short_exposure,
                "realized_pnl": realized_pnl,
                "unrealized_pnl": unrealized_pnl,
                "position_count": len(positions),
                "as_of": summary.get("snapshot_time") or summary.get("as_of"),
                "reporting_currency": summary.get("reporting_currency", "USD"),
            },
            "positions": positions,
        }

    async def get_positions_table(self) -> dict[str, Any]:
        payload = await self._get_v12_positions_latest()
        positions = payload.get("items", payload.get("positions", []))

        rows = []
        for p in positions:
            rows.append(
                {
                    "symbol": p.get("symbol"),
                    "strategy_id": p.get("strategy_id"),
                    "alpha_family": p.get("alpha_family"),
                    "side": p.get("side", "flat"),
                    "qty": p.get("abs_qty", abs(float(p.get("signed_qty", 0.0) or 0.0))),
                    "signed_qty": p.get("signed_qty", 0.0),
                    "avg_entry_price": p.get("avg_entry_price"),
                    "mark_price": p.get("mark_price"),
                    "market_value": p.get("market_value", 0.0),
                    "realized_pnl": p.get("realized_pnl", 0.0),
                    "unrealized_pnl": p.get("unrealized_pnl", 0.0),
                    "updated_at": p.get("updated_at"),
                }
            )

        return {"status": "ok", "items": rows}

    async def _get_v12_positions_latest(self) -> dict[str, Any]:
        for method_name in (
            "get_portfolio_positions_latest",
            "get_positions_latest",
            "get_portfolio_positions",
        ):
            method = getattr(self.v12_client, method_name, None)
            if callable(method):
                return await method()
        return {"status": "ok", "items": []}

    async def _get_v12_equity_latest(self) -> dict[str, Any]:
        for method_name in (
            "get_portfolio_equity_latest",
            "get_equity_latest",
            "get_portfolio_overview_summary_latest",
            "get_portfolio_overview",
        ):
            method = getattr(self.v12_client, method_name, None)
            if callable(method):
                payload = await method()
                if isinstance(payload, dict) and "summary" in payload and isinstance(payload["summary"], dict):
                    return dict(payload["summary"])
                return payload if isinstance(payload, dict) else {}
        return {"status": "ok"}