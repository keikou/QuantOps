from __future__ import annotations

from app.services.risk_service import RiskService


async def run_risk_snapshot_job(service: RiskService) -> dict:
    return await service.refresh_snapshot()
