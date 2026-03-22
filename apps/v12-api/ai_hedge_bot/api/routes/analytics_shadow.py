from __future__ import annotations

from fastapi import APIRouter
from ai_hedge_bot.app.container import CONTAINER

router = APIRouter(prefix='/analytics', tags=['analytics-shadow'])


@router.get('/shadow-summary')
def shadow_summary() -> dict:
    return CONTAINER.sprint5d_service.shadow_summary()
