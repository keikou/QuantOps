from __future__ import annotations

from app.clients.v12_client import V12Client, utc_now_iso
from app.repositories.risk_repository import RiskRepository


class RiskService:
    def __init__(self, v12_client: V12Client, risk_repository: RiskRepository) -> None:
        self.v12_client = v12_client
        self.risk_repository = risk_repository

    def _empty_snapshot(self) -> dict:
        return {
            "gross_exposure": 0.0,
            "net_exposure": 0.0,
            "leverage": 0.0,
            "drawdown": 0.0,
            "var_95": None,
            "stress_loss": None,
            "risk_limit": {
                "gross_exposure": 1.0,
                "drawdown": 0.0,
                "max_budget_usage": 1.0,
                "min_fill_rate": 0.85,
                "max_slippage_bps": 10.0,
                "kept_signals": 0,
                "global_alerts": [],
            },
            "alert_state": "unknown",
            "as_of": utc_now_iso(),
        }

    async def build_snapshot(self) -> dict:
        risk_budget = await self.v12_client.get_risk_budget()
        execution = await self.v12_client.get_execution_quality()
        diagnostics = await self.v12_client.get_portfolio_diagnostics()

        risk = risk_budget.get("risk", {})
        global_risk = risk_budget.get("global", {})
        per_strategy = risk.get("per_strategy", [])
        max_usage = max([float(item.get("budget_usage", 0.0) or 0.0) for item in per_strategy] or [0.0])
        drawdown = max(0.0, round(max_usage - 1.0, 6))
        gross = float(risk.get("gross_exposure", 0.0) or 0.0)
        net = float(risk.get("net_exposure", 0.0) or 0.0)
        fill_rate = execution.get("fill_rate")
        slippage = execution.get("avg_slippage_bps")
        kept_signals = (diagnostics.get("diagnostics") or diagnostics.get("latest") or {}).get("kept_signals", 0)
        risk_limit = {
            "gross_exposure": 1.0,
            "drawdown": 0.0,
            "max_budget_usage": 1.0,
            "min_fill_rate": 0.85,
            "max_slippage_bps": 10.0,
        }
        alert_state = "ok"
        if gross > risk_limit["gross_exposure"] or drawdown > risk_limit["drawdown"] or max_usage > risk_limit["max_budget_usage"]:
            alert_state = "breach"
        elif (fill_rate is not None and float(fill_rate) < risk_limit["min_fill_rate"]) or (
            slippage is not None and float(slippage) > risk_limit["max_slippage_bps"]
        ):
            alert_state = "warning"
        if global_risk.get("status") == "warning" and alert_state == "ok":
            alert_state = "warning"
        return {
            "gross_exposure": gross,
            "net_exposure": net,
            "leverage": gross,
            "drawdown": drawdown,
            "var_95": None,
            "stress_loss": None,
            "risk_limit": {**risk_limit, "kept_signals": kept_signals, "global_alerts": global_risk.get("alerts", [])},
            "alert_state": alert_state,
            "as_of": risk_budget.get("as_of") or execution.get("as_of") or utc_now_iso(),
        }

    async def get_snapshot(self) -> dict:
        latest = self.risk_repository.latest_snapshot()
        if latest is not None:
            return latest
        try:
            snapshot = await self.build_snapshot()
            self.risk_repository.insert_snapshot(snapshot)
            return snapshot
        except Exception:
            return self._empty_snapshot()

    async def refresh_snapshot(self) -> dict:
        try:
            snapshot = await self.build_snapshot()
            self.risk_repository.insert_snapshot(snapshot)
            return snapshot
        except Exception:
            latest = self.risk_repository.latest_snapshot()
            return latest if latest is not None else self._empty_snapshot()

    async def get_exposure(self) -> dict:
        snapshot = await self.get_snapshot()
        return {
            "gross_exposure": snapshot["gross_exposure"],
            "net_exposure": snapshot["net_exposure"],
            "leverage": snapshot["leverage"],
            "alert_state": snapshot["alert_state"],
            "as_of": snapshot["as_of"],
        }

    async def get_drawdown(self) -> dict:
        snapshot = await self.get_snapshot()
        return {"drawdown": snapshot["drawdown"], "risk_limit": snapshot["risk_limit"], "as_of": snapshot["as_of"]}
