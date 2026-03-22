from __future__ import annotations

from app.clients.v12_client import V12Client, utc_now_iso
from app.repositories.monitoring_repository import MonitoringRepository


class MonitoringService:
    def __init__(self, v12_client: V12Client, repository: MonitoringRepository) -> None:
        self.v12_client = v12_client
        self.repository = repository

    async def refresh(self) -> dict:
        health = await self.v12_client.get_system_health()
        execution = await self.v12_client.get_shadow_summary()
        payload = {
            "system_status": health.get("status", "unknown"),
            "execution_status": execution.get("status", "unknown"),
            "services": health.get("services", {}),
            "system": health,
            "execution": execution,
            "as_of": health.get("as_of") or execution.get("as_of") or utc_now_iso(),
        }
        return self.repository.insert_snapshot(payload)

    async def get_system(self) -> dict:
        payload = self.repository.latest_snapshot()
        if payload is None:
            payload = await self.refresh()
        return {"status": payload.get("system_status", "unknown"), "services": payload.get("services", {}), "as_of": payload.get("as_of") or utc_now_iso()}

    async def get_execution(self) -> dict:
        payload = self.repository.latest_snapshot()
        if payload is None:
            payload = await self.refresh()
        return {"status": payload.get("execution_status", "unknown"), "execution": payload.get("execution", {}), "as_of": payload.get("as_of") or utc_now_iso()}

    async def get_services(self) -> dict:
        payload = self.repository.latest_snapshot()
        if payload is None:
            payload = await self.refresh()
        return {"items": self.repository.latest_service_statuses(), "as_of": payload.get("as_of") or utc_now_iso()}
