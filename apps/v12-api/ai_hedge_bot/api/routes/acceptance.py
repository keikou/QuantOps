from __future__ import annotations

from fastapi import APIRouter
from ai_hedge_bot.app.container import CONTAINER

router = APIRouter(prefix='/acceptance', tags=['acceptance'])


@router.get('/status')
def acceptance_status(run_id: str | None = None) -> dict:
    return CONTAINER.sprint5d_service.acceptance_status(run_id=run_id)


@router.get('/checks')
def acceptance_checks(run_id: str | None = None) -> dict:
    return {'checks': CONTAINER.sprint5d_service.acceptance_checks(run_id=run_id)}


@router.post('/run')
def acceptance_run(payload: dict | None = None) -> dict:
    payload = payload or {}
    run_id = payload.get('run_id')
    mode = payload.get('mode')
    if mode and not run_id:
        run = CONTAINER.sprint5d_service.run_with_mode(payload)
        run_id = run['run_id']
    return CONTAINER.sprint5d_service.acceptance_status(run_id=run_id)
