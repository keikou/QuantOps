from __future__ import annotations

from fastapi import APIRouter

from ai_hedge_bot.app.container import CONTAINER

router = APIRouter(prefix='/risk', tags=['risk'])


@router.get('/latest')
def risk_latest() -> dict:
    return CONTAINER.sprint5c_service.get_latest_risk()


@router.get('/history')
def risk_history(limit: int = 100) -> list[dict]:
    return CONTAINER.sprint5c_service.get_risk_history(limit=limit)
