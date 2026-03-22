from __future__ import annotations

from fastapi import APIRouter, Depends

from app.core.deps import get_monitoring_service
from app.schemas.monitoring import MonitoringExecutionResponse, MonitoringServicesResponse, MonitoringSystemResponse
from app.services.monitoring_service import MonitoringService

router = APIRouter()

@router.post('/refresh')
async def refresh(service: MonitoringService = Depends(get_monitoring_service)) -> dict:
    return await service.refresh()

@router.get('/system', response_model=MonitoringSystemResponse)
async def system(service: MonitoringService = Depends(get_monitoring_service)) -> MonitoringSystemResponse:
    return MonitoringSystemResponse(**await service.get_system())

@router.get('/execution', response_model=MonitoringExecutionResponse)
async def execution(service: MonitoringService = Depends(get_monitoring_service)) -> MonitoringExecutionResponse:
    return MonitoringExecutionResponse(**await service.get_execution())

@router.get('/services', response_model=MonitoringServicesResponse)
async def services(service: MonitoringService = Depends(get_monitoring_service)) -> MonitoringServicesResponse:
    return MonitoringServicesResponse(**await service.get_services())
