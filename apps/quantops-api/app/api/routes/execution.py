from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.core.deps import get_execution_service
from app.services.execution_service import ExecutionService

router = APIRouter()


@router.get('/planner/latest')
async def execution_planner_latest(service: ExecutionService = Depends(get_execution_service)) -> dict:
    return await service.get_planner_latest()


@router.get('/view/latest')
async def execution_view_latest(service: ExecutionService = Depends(get_execution_service)) -> dict:
    return await service.get_view_latest()


@router.get('/orders')
async def execution_orders(limit: int = Query(default=100, ge=1, le=500), service: ExecutionService = Depends(get_execution_service)) -> dict:
    return await service.get_orders(limit=limit)


@router.get('/fills')
async def execution_fills(limit: int = Query(default=100, ge=1, le=500), service: ExecutionService = Depends(get_execution_service)) -> dict:
    return await service.get_fills(limit=limit)


@router.get('/state/latest')
async def execution_state_latest(service: ExecutionService = Depends(get_execution_service)) -> dict:
    return await service.get_state_latest()


@router.get('/block-reasons/latest')
async def execution_block_reasons_latest(service: ExecutionService = Depends(get_execution_service)) -> dict:
    return await service.get_block_reasons_latest()
