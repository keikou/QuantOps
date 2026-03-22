from __future__ import annotations

from app.clients.v12_client import V12Client, utc_now_iso
from app.repositories.scheduler_repository import SchedulerRepository


class DashboardService:
    def __init__(self, v12_client: V12Client, scheduler_repository: SchedulerRepository) -> None:
        self.v12_client = v12_client
        self.scheduler_repository = scheduler_repository

    async def get_overview(self) -> dict:
        global_dash = await self.v12_client.get_global_dashboard()
        strategy_registry = await self.v12_client.get_strategy_registry()
        execution_quality = await self.v12_client.get_execution_quality()
        cards = global_dash.get("cards", {})
        aggregate = (global_dash.get("strategy") or {}).get("aggregate", {})
        latest_risk = (global_dash.get("strategy") or {}).get("latest_risk_snapshot", {})
        alerts = (global_dash.get("strategy") or {}).get("drawdown_events", [])
        return {
            "portfolio_value": float(cards.get("allocated_capital", aggregate.get("allocated_capital", 0.0)) or 0.0),
            "pnl": float(aggregate.get("avg_realized_return", 0.0) or 0.0),
            "gross_exposure": float(latest_risk.get("gross_exposure", 0.0) or 0.0),
            "net_exposure": float(latest_risk.get("net_exposure", 0.0) or 0.0),
            "leverage": float(latest_risk.get("gross_exposure", 0.0) or 0.0),
            "active_strategies": int(strategy_registry.get("enabled_count", cards.get("strategy_count", 0)) or 0),
            "alerts": alerts,
            "as_of": (
                global_dash.get("as_of")
                or execution_quality.get("as_of")
                or strategy_registry.get("as_of")
                or utc_now_iso()
            ),
        }

    async def get_system_health(self) -> dict:
        payload = await self.v12_client.get_system_health()
        services = payload.get("services")
        if not isinstance(services, dict):
            services = {
                "api": "ok" if payload.get("status") == "ok" else "unknown",
                "runtime": payload.get("mode", "unknown"),
                "phase": payload.get("phase"),
                "sprint": payload.get("sprint"),
            }
        return {
            "status": payload.get("status", "unknown"),
            "services": services,
            "as_of": payload.get("as_of") or utc_now_iso(),
        }

    def get_job_status(self) -> dict:
        return {"jobs": self.scheduler_repository.list_jobs()}
