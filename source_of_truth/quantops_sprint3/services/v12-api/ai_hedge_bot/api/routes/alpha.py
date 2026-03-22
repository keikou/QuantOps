from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Body

from ai_hedge_bot.autonomous_alpha.service import AutonomousAlphaService

router = APIRouter(prefix='/alpha', tags=['alpha'])
service = AutonomousAlphaService()


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
