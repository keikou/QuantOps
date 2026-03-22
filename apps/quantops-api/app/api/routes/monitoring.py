from __future__ import annotations

import time

from fastapi import APIRouter, Depends, Request

from app.core.deps import get_monitoring_service
from app.services.monitoring_service import MonitoringService

router = APIRouter()


@router.get('/system')
async def monitoring_system(request: Request, service: MonitoringService = Depends(get_monitoring_service)) -> dict:
    started = time.perf_counter()
    payload = await service.get_system()
    request.state.handler_duration_ms = round((time.perf_counter() - started) * 1000.0, 2)
    return payload


@router.post('/refresh')
async def monitoring_refresh(service: MonitoringService = Depends(get_monitoring_service)) -> dict:
    return await service.refresh()


@router.get('/debug/system')
async def monitoring_system_debug(request: Request, service: MonitoringService = Depends(get_monitoring_service)) -> dict:
    started = time.perf_counter()
    payload = await service.get_system_debug()
    request.state.handler_duration_ms = round((time.perf_counter() - started) * 1000.0, 2)
    return payload


@router.get('/execution')
async def monitoring_execution(request: Request, service: MonitoringService = Depends(get_monitoring_service)) -> dict:
    started = time.perf_counter()
    payload = await service.get_execution()
    request.state.handler_duration_ms = round((time.perf_counter() - started) * 1000.0, 2)
    return payload


@router.get('/services')
async def monitoring_services(request: Request, service: MonitoringService = Depends(get_monitoring_service)) -> dict:
    started = time.perf_counter()
    payload = await service.get_services()
    request.state.handler_duration_ms = round((time.perf_counter() - started) * 1000.0, 2)
    return payload
