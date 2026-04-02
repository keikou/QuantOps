from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Body

from ai_hedge_bot.autonomous_alpha.service import AutonomousAlphaService
from ai_hedge_bot.services.alpha_strategy_selection_intelligence_service import (
    AlphaStrategySelectionIntelligenceService,
)

router = APIRouter(prefix='/alpha', tags=['alpha'])
service = AutonomousAlphaService()
selection_service = AlphaStrategySelectionIntelligenceService()


@router.get('/overview')
def overview() -> dict[str, Any]:
    return service.overview()


@router.get('/registry')
def registry(limit: int = 50) -> dict[str, Any]:
    return {'status': 'ok', 'registry': service.library(limit=limit)}


@router.post('/generate')
def generate(payload: dict[str, Any] = Body(default_factory=dict)) -> dict[str, Any]:
    return {'status': 'ok', **service.generate(payload)}


@router.post('/test')
def test_alpha(payload: dict[str, Any] = Body(default_factory=dict)) -> dict[str, Any]:
    return {'status': 'ok', 'result': service.test(payload)}


@router.post('/evaluate')
def evaluate_alpha(payload: dict[str, Any] = Body(default_factory=dict)) -> dict[str, Any]:
    return {'status': 'ok', 'ranking': service.evaluate(payload)}


@router.get('/ranking')
def ranking(limit: int = 20) -> dict[str, Any]:
    return {'status': 'ok', 'ranking': service.ranking(limit=limit)}


@router.get('/library')
def library(limit: int = 50) -> dict[str, Any]:
    return {'status': 'ok', 'library': service.library(limit=limit)}


@router.get('/intelligence/selection/latest')
def alpha_strategy_selection_latest(limit: int = 20) -> dict[str, Any]:
    return selection_service.selection_latest(limit=limit)


@router.get('/intelligence/strategy-actions/latest')
def alpha_strategy_actions_latest(limit: int = 20) -> dict[str, Any]:
    return selection_service.strategy_action_latest(limit=limit)


@router.get('/intelligence/selection-queues/latest')
def alpha_selection_queues_latest(limit: int = 20) -> dict[str, Any]:
    return selection_service.selection_queue_latest(limit=limit)


@router.get('/intelligence/family-budget-arbitration/latest')
def alpha_family_budget_arbitration_latest(limit: int = 20) -> dict[str, Any]:
    return selection_service.family_budget_arbitration_latest(limit=limit)


@router.get('/intelligence/effective-selection-slate/latest')
def alpha_effective_selection_slate_latest(limit: int = 20) -> dict[str, Any]:
    return selection_service.effective_selection_slate_latest(limit=limit)
