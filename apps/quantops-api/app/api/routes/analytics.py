from __future__ import annotations

from fastapi import APIRouter, Depends
import logging

from app.core.deps import get_analytics_service, get_v12_client
from app.clients.v12_client import V12Client, utc_now_iso
from app.services.analytics_service import AnalyticsService

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post('/refresh')
async def refresh(service: AnalyticsService = Depends(get_analytics_service)) -> dict:
    return await service.refresh()


@router.get('/summary')
async def analytics_summary(service: AnalyticsService = Depends(get_analytics_service)) -> dict:
    ranking = service.alpha_ranking()
    items = ranking.get('items', [])
    return {
        'status': 'ok',
        'summary': {
            'alpha_count': ranking.get('count', 0),
            'best_alpha': items[0] if items else None,
            'worst_alpha': items[-1] if items else None,
            'as_of': ranking.get('as_of'),
        },
    }


@router.get('/alpha')
async def alpha(service: AnalyticsService = Depends(get_analytics_service)) -> dict:
    return service.alpha_ranking()


@router.get('/pnl-summary')
async def pnl_summary(service: AnalyticsService = Depends(get_analytics_service)) -> dict:
    return service.pnl_summary()


@router.get('/sharpe-summary')
async def sharpe_summary(service: AnalyticsService = Depends(get_analytics_service)) -> dict:
    return service.sharpe_summary()


@router.get('/drawdown-summary')
async def drawdown_summary(service: AnalyticsService = Depends(get_analytics_service)) -> dict:
    return service.drawdown_summary()


@router.get('/execution-summary')
async def execution_summary(service: AnalyticsService = Depends(get_analytics_service)) -> dict:
    try:
        payload = await service.execution_summary_live()
        payload.setdefault('status', 'ok')
        payload.setdefault('degraded', False)
        payload.setdefault('as_of', payload.get('as_of'))
        return payload
    except Exception as exc:  # pragma: no cover - defensive production fallback
        logger.exception('execution_summary fallback activated: %s', exc)
        return {
            'status': 'ok',
            'degraded': True,
            'fill_rate': 0.0,
            'avg_slippage_bps': 0.0,
            'latency_ms_p50': 0.0,
            'latency_ms_p95': 0.0,
            'venue_score': 0.0,
            'as_of': utc_now_iso(),
            'message': 'execution summary fallback returned due to upstream read failure',
        }


@router.get('/runtime-states')
async def runtime_states(service: AnalyticsService = Depends(get_analytics_service)) -> list[dict]:
    return service.runtime_states()


@router.get('/performance')
async def performance(client: V12Client = Depends(get_v12_client)) -> dict:
    return await client.get_sprint5c_analytics_performance()


@router.get('/equity-history')
async def equity_history(service: AnalyticsService = Depends(get_analytics_service)) -> dict:
    return await service.equity_history()


@router.get('/execution-latest')
async def execution_latest(service: AnalyticsService = Depends(get_analytics_service)) -> dict:
    return await service.latest_execution_fills()


@router.get('/execution-planner-latest')
async def execution_planner_latest(service: AnalyticsService = Depends(get_analytics_service)) -> dict:
    return await service.latest_execution_planner()
