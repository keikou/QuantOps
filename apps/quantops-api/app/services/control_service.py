from __future__ import annotations

from app.clients.v12_client import V12Client
from app.repositories.analytics_repository import AnalyticsRepository
from app.repositories.audit_repository import AuditRepository
from app.repositories.risk_repository import RiskRepository


class ControlService:
    def __init__(self, v12_client: V12Client, audit_repository: AuditRepository, analytics_repository: AnalyticsRepository, risk_repository: RiskRepository) -> None:
        self.v12_client = v12_client
        self.audit_repository = audit_repository
        self.analytics_repository = analytics_repository
        self.risk_repository = risk_repository

    async def _runtime_action(self, action: str, strategy_id: str, desired_state: str) -> dict:
        result = await self.v12_client.unsupported_action(action, {"strategy_id": strategy_id})
        remote_status = str(result.get("status", "unknown") or "unknown")
        ok = remote_status in {"ok", "accepted", "submitted", "queued"}
        runtime_state = self.analytics_repository.upsert_runtime_state(
            strategy_id=strategy_id,
            desired_state=desired_state,
            remote_status=remote_status,
            note=("Applied via V12 lifecycle adapter" if ok else "Lifecycle adapter unavailable"),
        )
        payload = {"result": result, "runtime_state": runtime_state}
        self.audit_repository.log_action(category="control", event_type=action, payload_json=str(payload))
        return {"ok": ok, "action": action, "target": strategy_id, **payload}

    async def start_strategy(self, strategy_id: str) -> dict:
        return await self._runtime_action("start_strategy", strategy_id, "running")

    async def stop_strategy(self, strategy_id: str) -> dict:
        return await self._runtime_action("stop_strategy", strategy_id, "stopped")

    async def pause_strategy(self, strategy_id: str) -> dict:
        return await self._runtime_action("pause_strategy", strategy_id, "paused")

    async def reload_strategy(self, strategy_id: str) -> dict:
        return await self._runtime_action("reload_strategy", strategy_id, "reloading")

    async def kill_switch(self) -> dict:
        result = await self.v12_client.unsupported_action("kill_switch")
        remote_status = str(result.get("status", "unknown") or "unknown")
        ok = remote_status in {"ok", "accepted", "submitted", "queued"}
        state = self.risk_repository.set_trading_state("halted", "Kill switch triggered from control service")
        self.audit_repository.log_action(category="control", event_type="kill_switch", payload_json=str({"result": result, "state": state}))
        return {"ok": ok, "action": "kill_switch", "target": "system", "result": result, "risk_state": state}

    async def rebalance(self) -> dict:
        allocation = await self.v12_client.allocate_capital()
        cycle = await self.v12_client.run_paper_cycle()
        result = {"allocate_capital": allocation, "paper_cycle": cycle}
        self.audit_repository.log_action(category="control", event_type="rebalance", payload_json=str(result))
        return {"ok": True, "action": "rebalance", "target": "portfolio", "result": result}

    async def allocate_capital(self, total_capital: float | None = None) -> dict:
        allocation = await self.v12_client.allocate_capital()
        result = {"requested_total_capital": total_capital, "allocation": allocation}
        self.audit_repository.log_action(category="control", event_type="allocate_capital", payload_json=str(result))
        return {"ok": True, "action": "allocate_capital", "target": "portfolio", "result": result}
