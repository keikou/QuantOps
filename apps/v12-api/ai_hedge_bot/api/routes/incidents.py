from __future__ import annotations

from fastapi import APIRouter
from ai_hedge_bot.app.container import CONTAINER

router = APIRouter(prefix='/incidents', tags=['incidents'])


@router.get('/latest')
def incidents_latest(limit: int = 20) -> dict:
    return {'incidents': CONTAINER.sprint5d_service.latest_incidents(limit=limit)}


@router.get('/history')
def incidents_history(limit: int = 100) -> dict:
    return {'incidents': CONTAINER.sprint5d_service.latest_incidents(limit=limit)}
