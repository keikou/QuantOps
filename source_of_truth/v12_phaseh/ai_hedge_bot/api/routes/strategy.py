from __future__ import annotations

from fastapi import APIRouter

from ai_hedge_bot.strategy.strategy_service import StrategyService

router = APIRouter(prefix='/strategy', tags=['strategy'])
_service = StrategyService()


@router.get('/registry')
def registry() -> dict:
    return _service.registry_view()


@router.post('/allocate-capital')
def allocate_capital() -> dict:
    return _service.allocate_capital()


@router.get('/risk-budget')
def risk_budget() -> dict:
    return _service.latest_risk_budget()
