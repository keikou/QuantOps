from __future__ import annotations

import time

from fastapi import APIRouter, Depends, Request

from app.core.deps import get_dashboard_service
from app.schemas.dashboard import DashboardOverviewResponse, SystemHealthResponse
from app.services.dashboard_service import DashboardService

router = APIRouter()


@router.get("/overview", response_model=DashboardOverviewResponse)
async def get_overview(request: Request, service: DashboardService = Depends(get_dashboard_service)) -> DashboardOverviewResponse:
    started = time.perf_counter()
    response = DashboardOverviewResponse(**await service.get_overview())
    request.state.handler_duration_ms = round((time.perf_counter() - started) * 1000.0, 2)
    return response


@router.get("/debug/overview")
async def get_overview_debug(request: Request, service: DashboardService = Depends(get_dashboard_service)) -> dict:
    started = time.perf_counter()
    payload = await service.get_overview_debug()
    request.state.handler_duration_ms = round((time.perf_counter() - started) * 1000.0, 2)
    return payload


@router.get("/system-health", response_model=SystemHealthResponse)
async def get_system_health(service: DashboardService = Depends(get_dashboard_service)) -> SystemHealthResponse:
    return SystemHealthResponse(**await service.get_system_health())


@router.get("/job-status")
def get_job_status(service: DashboardService = Depends(get_dashboard_service)) -> dict:
    return service.get_job_status()
