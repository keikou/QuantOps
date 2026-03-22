from __future__ import annotations

from fastapi import APIRouter
from ai_hedge_bot.analytics.analytics_service import AnalyticsService
from ai_hedge_bot.app.container import CONTAINER

router = APIRouter(prefix='/analytics', tags=['analytics'])
service = AnalyticsService()

@router.get('/signal-summary')
def analytics_signal_summary() -> dict:
    return service.signal_summary()

@router.get('/portfolio-summary')
def analytics_portfolio_summary() -> dict:
    return service.portfolio_summary()

@router.get('/shadow-summary')
def analytics_shadow_summary() -> dict:
    summary = CONTAINER.sprint5d_service.shadow_summary()
    if summary.get('status') == 'missing':
        return service.shadow_summary()
    return summary

@router.get('/execution-quality')
def analytics_execution_quality() -> dict:
    return service.execution_quality()

@router.get('/mode-comparison')
def analytics_mode_comparison() -> dict:
    return service.mode_comparison()

@router.get('/strategy-summary')
def analytics_strategy_summary() -> dict:
    return service.strategy_summary()
