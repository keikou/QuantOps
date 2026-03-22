from __future__ import annotations

from fastapi import APIRouter, Depends

from app.core.deps import get_control_service
from app.schemas.analytics import AllocationRequest, StrategyRuntimeRequest
from app.services.control_service import ControlService

router = APIRouter()


@router.post('/start-strategy')
async def start_strategy(payload: StrategyRuntimeRequest, service: ControlService = Depends(get_control_service)) -> dict:
    return await service.start_strategy(payload.strategy_id)


@router.post('/stop-strategy')
async def stop_strategy(payload: StrategyRuntimeRequest, service: ControlService = Depends(get_control_service)) -> dict:
    return await service.stop_strategy(payload.strategy_id)


@router.post('/pause-strategy')
async def pause_strategy(payload: StrategyRuntimeRequest, service: ControlService = Depends(get_control_service)) -> dict:
    return await service.pause_strategy(payload.strategy_id)


@router.post('/reload-strategy')
async def reload_strategy(payload: StrategyRuntimeRequest, service: ControlService = Depends(get_control_service)) -> dict:
    return await service.reload_strategy(payload.strategy_id)


@router.post('/allocate-capital')
async def allocate_capital(payload: AllocationRequest, service: ControlService = Depends(get_control_service)) -> dict:
    return await service.allocate_capital(payload.total_capital)


@router.post('/kill-switch')
async def kill_switch(service: ControlService = Depends(get_control_service)) -> dict:
    return await service.kill_switch()


@router.post('/rebalance')
async def rebalance(service: ControlService = Depends(get_control_service)) -> dict:
    return await service.rebalance()
