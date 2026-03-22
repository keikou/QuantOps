from __future__ import annotations

from app.clients.v12_client import V12Client, utc_now_iso


class PortfolioService:
    def __init__(self, v12_client: V12Client) -> None:
        self.v12_client = v12_client

    async def get_overview(self) -> dict:
        portfolio_dashboard = await self.v12_client.get_portfolio_dashboard()
        portfolio_analytics = await self.v12_client.get_portfolio_analytics()
        risk_budget = await self.v12_client.get_risk_budget()
        strategy_registry = await self.v12_client.get_strategy_registry()

        cards = portfolio_dashboard.get("cards", {})
        latest = portfolio_analytics.get("latest", {})
        risk = risk_budget.get("risk", {})
        positions = self._build_positions(strategy_registry.get("strategies", []))
        weights = {item["symbol"]: item["weight"] for item in positions}
        gross_exposure = float(risk.get("gross_exposure", cards.get("gross_exposure_estimate", 0.0)) or 0.0)
        net_exposure = float(risk.get("net_exposure", 0.0) or 0.0)
        long_exposure = sum(max(0.0, float(v)) for v in weights.values())
        short_exposure = sum(abs(min(0.0, float(v))) for v in weights.values())
        drawdown = max(
            [float(row.get("budget_usage", 0.0) or 0.0) - 1.0 for row in risk.get("per_strategy", [])] or [0.0]
        )

        return {
            "portfolio_value": float(cards.get("portfolio_count", 0) or 0),
            "cash": max(0.0, 1.0 - float(sum(abs(v) for v in weights.values()))),
            "pnl": float(latest.get("kept_signals", 0) or 0),
            "drawdown": float(drawdown),
            "gross_exposure": gross_exposure,
            "net_exposure": net_exposure,
            "long_exposure": round(long_exposure, 6),
            "short_exposure": round(short_exposure, 6),
            "leverage": gross_exposure,
            "weights": weights,
            "positions": positions,
            "as_of": (
                portfolio_dashboard.get("as_of")
                or portfolio_analytics.get("as_of")
                or risk_budget.get("as_of")
                or utc_now_iso()
            ),
        }

    async def get_positions(self) -> list[dict]:
        strategy_registry = await self.v12_client.get_strategy_registry()
        return self._build_positions(strategy_registry.get("strategies", []))

    async def get_exposure(self) -> dict:
        risk_budget = await self.v12_client.get_risk_budget()
        risk = risk_budget.get("risk", {})
        return {
            "gross_exposure": float(risk.get("gross_exposure", 0.0) or 0.0),
            "net_exposure": float(risk.get("net_exposure", 0.0) or 0.0),
            "long_exposure": float(risk.get("gross_exposure", 0.0) or 0.0),
            "short_exposure": 0.0,
            "leverage": float(risk.get("gross_exposure", 0.0) or 0.0),
            "as_of": risk_budget.get("as_of") or utc_now_iso(),
        }

    def _build_positions(self, strategies: list[dict]) -> list[dict]:
        positions: list[dict] = []
        for row in strategies:
            weight = float(row.get("capital_weight", 0.0) or 0.0)
            positions.append(
                {
                    "symbol": row.get("strategy_id", row.get("strategy_name", "unknown")),
                    "weight": weight,
                    "notional": round(weight * 1_000_000, 2),
                    "pnl": float(row.get("realized_return", row.get("expected_return", 0.0)) or 0.0),
                }
            )
        return positions
