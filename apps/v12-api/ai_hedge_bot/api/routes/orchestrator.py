from __future__ import annotations

from fastapi import APIRouter
from ai_hedge_bot.orchestrator.orchestration_service import OrchestrationService
from ai_hedge_bot.app.container import CONTAINER

router = APIRouter(prefix='/orchestrator', tags=['orchestrator'])
_service = OrchestrationService()


@router.post('/backtest/run')
def backtest_run() -> dict:
    return _service.run('backtest')


@router.post('/paper/run-cycle')
def paper_run_cycle() -> dict:
    return _service.run('paper')


@router.post('/shadow/run-cycle')
def shadow_run_cycle() -> dict:
    return _service.run('shadow')


@router.get('/runs/latest')
def latest_run() -> dict:
    if not CONTAINER.latest_orchestrator_run:
        return {'status': 'missing'}
    return {'status': 'ok', 'run': CONTAINER.latest_orchestrator_run}


@router.post('/state/snapshot/save')
def save_snapshot() -> dict:
    payload = {
        'status': 'ok',
        'mode': CONTAINER.mode.value,
        'symbols': CONTAINER.config.symbols,
        'latest_portfolio_diagnostics': CONTAINER.latest_portfolio_diagnostics,
        'latest_orchestrator_run': CONTAINER.latest_orchestrator_run,
    }
    path = CONTAINER.snapshot_service.save('latest', payload)
    return {'status': 'ok', 'path': path}


@router.post('/state/snapshot/restore')
def restore_snapshot() -> dict:
    payload = CONTAINER.snapshot_service.load('latest')
    if payload.get('status') == 'missing':
        return payload
    CONTAINER.latest_portfolio_diagnostics = payload.get('latest_portfolio_diagnostics', {})
    CONTAINER.latest_orchestrator_run = payload.get('latest_orchestrator_run', {})
    return {'status': 'ok', 'snapshot': payload}


@router.get('/state/snapshot/latest')
def latest_snapshot() -> dict:
    payload = CONTAINER.snapshot_service.load('latest')
    if payload.get('status') == 'missing':
        return payload
    return {'status': 'ok', 'snapshot': payload}
