from __future__ import annotations

from fastapi import APIRouter, HTTPException
from ai_hedge_bot.app.container import CONTAINER

router = APIRouter(tags=['runtime-sprint5d'])


@router.post('/runtime/run-with-mode')
def run_with_mode(payload: dict | None = None) -> dict:
    return CONTAINER.sprint5d_service.run_with_mode(payload)


@router.get('/runtime/modes')
def list_modes() -> dict:
    return {'modes': CONTAINER.sprint5d_service.list_modes()}


@router.get('/runtime/modes/current')
def current_mode() -> dict:
    return CONTAINER.sprint5d_service.get_current_mode()


@router.post('/runtime/modes/set')
def set_current_mode(payload: dict) -> dict:
    try:
        return CONTAINER.sprint5d_service.set_current_mode(str(payload.get('mode')))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get('/runtime/modes/runs/latest')
def latest_mode_run() -> dict:
    return CONTAINER.sprint5d_service.latest_run()
