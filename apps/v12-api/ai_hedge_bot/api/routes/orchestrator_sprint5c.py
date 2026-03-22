from __future__ import annotations

from fastapi import APIRouter

from ai_hedge_bot.app.container import CONTAINER

router = APIRouter(prefix='/runtime', tags=['runtime'])


@router.post('/run-sprint5c')
def run_sprint5c(payload: dict | None = None) -> dict:
    return CONTAINER.sprint5c_service.run_once(payload)
