from __future__ import annotations

import time

from fastapi import APIRouter, Depends, Request

from app.core.deps import get_risk_service, get_v12_client
from app.schemas.risk import RiskSnapshotResponse
from app.services.risk_service import RiskService
from app.clients.v12_client import V12Client

router = APIRouter()

@router.get('/snapshot', response_model=RiskSnapshotResponse)
async def snapshot(request: Request, service: RiskService = Depends(get_risk_service)) -> RiskSnapshotResponse:
    started = time.perf_counter()
    response = RiskSnapshotResponse(**await service.get_snapshot())
    request.state.handler_duration_ms = round((time.perf_counter() - started) * 1000.0, 2)
    return response

@router.post('/refresh', response_model=RiskSnapshotResponse)
async def refresh(request: Request, service: RiskService = Depends(get_risk_service)) -> RiskSnapshotResponse:
    started = time.perf_counter()
    response = RiskSnapshotResponse(**await service.refresh_snapshot())
    request.state.handler_duration_ms = round((time.perf_counter() - started) * 1000.0, 2)
    return response

@router.get('/debug/snapshot')
async def snapshot_debug(request: Request, service: RiskService = Depends(get_risk_service)) -> dict:
    started = time.perf_counter()
    payload = await service.get_snapshot_debug()
    request.state.handler_duration_ms = round((time.perf_counter() - started) * 1000.0, 2)
    return payload

@router.get('/exposure')
async def exposure(service: RiskService = Depends(get_risk_service)) -> dict:
    return await service.get_exposure()

@router.get('/drawdown')
async def drawdown(service: RiskService = Depends(get_risk_service)) -> dict:
    return await service.get_drawdown()

@router.get('/latest')
async def latest(client: V12Client = Depends(get_v12_client)) -> dict:
    return await client.get_sprint5c_risk_latest()

@router.get('/history')
async def history(limit: int = 100, client: V12Client = Depends(get_v12_client)) -> dict:
    return await client.get_sprint5c_risk_history(limit=limit)
