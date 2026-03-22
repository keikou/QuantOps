from __future__ import annotations

from fastapi import APIRouter, Depends

from app.core.deps import get_dashboard_service
from app.schemas.dashboard import DashboardOverviewResponse, SystemHealthResponse
from app.services.dashboard_service import DashboardService

router = APIRouter()


@router.get("/overview", response_model=DashboardOverviewResponse)
async def get_overview(service: DashboardService = Depends(get_dashboard_service)) -> DashboardOverviewResponse:
    return DashboardOverviewResponse(**await service.get_overview())


@router.get("/system-health", response_model=SystemHealthResponse)
async def get_system_health(service: DashboardService = Depends(get_dashboard_service)) -> SystemHealthResponse:
    return SystemHealthResponse(**await service.get_system_health())


@router.get("/job-status")
def get_job_status(service: DashboardService = Depends(get_dashboard_service)) -> dict:
    return service.get_job_status()
