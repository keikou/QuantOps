from __future__ import annotations

from fastapi import APIRouter, Depends

from app.core.deps import get_risk_service
from app.schemas.risk import RiskSnapshotResponse
from app.services.risk_service import RiskService

router = APIRouter()


@router.get("/snapshot", response_model=RiskSnapshotResponse)
async def snapshot(service: RiskService = Depends(get_risk_service)) -> RiskSnapshotResponse:
    return RiskSnapshotResponse(**await service.get_snapshot())


@router.post("/refresh", response_model=RiskSnapshotResponse)
async def refresh(service: RiskService = Depends(get_risk_service)) -> RiskSnapshotResponse:
    return RiskSnapshotResponse(**await service.refresh_snapshot())


@router.get("/exposure")
async def exposure(service: RiskService = Depends(get_risk_service)) -> dict:
    return await service.get_exposure()


@router.get("/drawdown")
async def drawdown(service: RiskService = Depends(get_risk_service)) -> dict:
    return await service.get_drawdown()
