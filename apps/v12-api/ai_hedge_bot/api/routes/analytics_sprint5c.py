from __future__ import annotations

from fastapi import APIRouter

from ai_hedge_bot.app.container import CONTAINER

router = APIRouter(prefix='/analytics', tags=['analytics'])


@router.get('/performance')
def analytics_performance() -> dict:
    return CONTAINER.sprint5c_service.get_latest_performance()


@router.get('/alpha')
def analytics_alpha() -> dict:
    return CONTAINER.sprint5c_service.get_latest_alpha_metrics()
