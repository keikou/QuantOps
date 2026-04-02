from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Body

from ai_hedge_bot.research_factory.service import ResearchFactoryService
from ai_hedge_bot.services.research_promotion_intelligence_service import (
    ResearchPromotionIntelligenceService,
)

router = APIRouter(prefix='/research-factory', tags=['research-factory'])
service = ResearchFactoryService()
intelligence_service = ResearchPromotionIntelligenceService()


@router.get('/overview')
def overview() -> dict[str, Any]:
    return service.overview()


@router.get('/governance-overview')
def governance_overview() -> dict[str, Any]:
    return service.governance_overview()


@router.post('/experiments/register')
def register_experiment(payload: dict[str, Any] = Body(default_factory=dict)) -> dict[str, Any]:
    return service.register_experiment(payload)


@router.post('/datasets/register')
def register_dataset(payload: dict[str, Any] = Body(default_factory=dict)) -> dict[str, Any]:
    return service.register_dataset(payload)


@router.post('/features/register')
def register_feature(payload: dict[str, Any] = Body(default_factory=dict)) -> dict[str, Any]:
    return service.register_feature(payload)


@router.post('/validations/register')
def register_validation(payload: dict[str, Any] = Body(default_factory=dict)) -> dict[str, Any]:
    return service.register_validation(payload)


@router.post('/models/register')
def register_model(payload: dict[str, Any] = Body(default_factory=dict)) -> dict[str, Any]:
    return service.register_model(payload)


@router.post('/promotion/evaluate')
def evaluate_promotion(payload: dict[str, Any] = Body(default_factory=dict)) -> dict[str, Any]:
    return service.evaluate_promotion(payload)


@router.get('/live-review')
def live_review() -> dict[str, Any]:
    return service.latest_live_review()


@router.get('/alpha-decay')
def alpha_decay() -> dict[str, Any]:
    return service.latest_alpha_decay()


@router.post('/rollback/evaluate')
def evaluate_rollback(payload: dict[str, Any] = Body(default_factory=dict)) -> dict[str, Any]:
    return service.evaluate_rollback(payload)


@router.post('/champion-challenger/run')
def champion_challenger_run(payload: dict[str, Any] = Body(default_factory=dict)) -> dict[str, Any]:
    return service.run_champion_challenger(payload)


@router.get('/intelligence/promotion-agenda/latest')
def promotion_agenda_latest(limit: int = 20) -> dict[str, Any]:
    return intelligence_service.promotion_agenda_latest(limit=limit)


@router.get('/intelligence/promotion-candidate-docket/latest')
def promotion_candidate_docket_latest(limit: int = 20) -> dict[str, Any]:
    return intelligence_service.promotion_candidate_docket_latest(limit=limit)


@router.get('/intelligence/review-queues/latest')
def review_queues_latest(limit: int = 20) -> dict[str, Any]:
    return intelligence_service.review_queues_latest(limit=limit)


@router.get('/intelligence/review-board-slate/latest')
def review_board_slate_latest(limit: int = 20) -> dict[str, Any]:
    return intelligence_service.review_board_slate_latest(limit=limit)


@router.get('/intelligence/deterministic-review-outcomes/latest')
def deterministic_review_outcomes_latest(limit: int = 20) -> dict[str, Any]:
    return intelligence_service.deterministic_review_outcomes_latest(limit=limit)


@router.get('/intelligence/persisted-governed-state-transitions/latest')
def persisted_governed_state_transitions_latest(limit: int = 20) -> dict[str, Any]:
    return intelligence_service.persisted_governed_state_transitions_latest(limit=limit)
