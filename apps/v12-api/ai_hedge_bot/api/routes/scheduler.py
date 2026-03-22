from __future__ import annotations

from fastapi import APIRouter, Query

from ai_hedge_bot.services.runtime.runtime_service import RuntimeService

router = APIRouter(prefix='/scheduler', tags=['scheduler'])
_service = RuntimeService()


@router.get('/jobs')
def list_jobs() -> dict:
    return {'status': 'ok', 'items': _service.list_scheduler_jobs()}


@router.get('/runs')
def list_runs(limit: int = Query(default=20, ge=1, le=100)) -> dict:
    return {'status': 'ok', 'items': _service.list_scheduler_runs(limit=limit)}
