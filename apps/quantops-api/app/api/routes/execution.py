from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.core.deps import get_v12_client
from app.services.execution_service import ExecutionService
from app.clients.v12_client import V12Client

router = APIRouter()


def _svc(client: V12Client = Depends(get_v12_client)) -> ExecutionService:
    return ExecutionService(client)


@router.get('/planner/latest')
async def execution_planner_latest(service: ExecutionService = Depends(_svc)) -> dict:
    return await service.get_planner_latest()


@router.get('/orders')
async def execution_orders(limit: int = Query(default=100, ge=1, le=500), service: ExecutionService = Depends(_svc)) -> dict:
    return await service.get_orders(limit=limit)


@router.get('/fills')
async def execution_fills(limit: int = Query(default=100, ge=1, le=500), service: ExecutionService = Depends(_svc)) -> dict:
    return await service.get_fills(limit=limit)


@router.get('/state/latest')
async def execution_state_latest(service: ExecutionService = Depends(_svc)) -> dict:
    return await service.get_state_latest()


@router.get('/block-reasons/latest')
async def execution_block_reasons_latest(service: ExecutionService = Depends(_svc)) -> dict:
    return await service.get_block_reasons_latest()
