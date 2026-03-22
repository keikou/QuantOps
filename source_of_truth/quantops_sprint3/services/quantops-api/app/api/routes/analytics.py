from __future__ import annotations

from fastapi import APIRouter, Depends

from app.core.deps import get_analytics_service
from app.services.analytics_service import AnalyticsService

router = APIRouter()


@router.post('/refresh')
async def refresh(service: AnalyticsService = Depends(get_analytics_service)) -> dict:
    return await service.refresh()


@router.get('/alpha')
def alpha(service: AnalyticsService = Depends(get_analytics_service)) -> dict:
    return service.alpha_ranking()


@router.get('/pnl')
def pnl(service: AnalyticsService = Depends(get_analytics_service)) -> dict:
    return service.pnl_summary()


@router.get('/sharpe')
def sharpe(service: AnalyticsService = Depends(get_analytics_service)) -> dict:
    return service.sharpe_summary()


@router.get('/drawdown')
def drawdown(service: AnalyticsService = Depends(get_analytics_service)) -> dict:
    return service.drawdown_summary()


@router.get('/execution')
def execution(service: AnalyticsService = Depends(get_analytics_service)) -> dict:
    return service.execution_summary()


@router.get('/runtime-states')
def runtime_states(service: AnalyticsService = Depends(get_analytics_service)) -> list[dict]:
    return service.runtime_states()
