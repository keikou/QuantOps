from __future__ import annotations

from fastapi import APIRouter

from ai_hedge_bot.app.container import CONTAINER

router = APIRouter(prefix='/governance', tags=['governance'])


@router.get('/budgets')
def governance_budgets() -> list[dict]:
    return CONTAINER.sprint5c_service.get_latest_budgets()


@router.get('/regime')
def governance_regime() -> dict:
    return CONTAINER.sprint5c_service.get_latest_regime()
