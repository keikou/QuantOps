from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from ai_hedge_bot.app.container import CONTAINER
from ai_hedge_bot.services.runtime.runtime_service import RuntimeService

router = APIRouter(prefix='/runtime', tags=['runtime'])
_service = RuntimeService()


@router.post('/run-once')
def run_once(mode: str | None = None) -> dict:
    return _service.run_once(mode=mode)


@router.get('/runs')
def list_runs(limit: int = Query(default=20, ge=1, le=100)) -> dict:
    return {'status': 'ok', 'items': _service.list_runs(limit=limit)}


@router.get('/runs/{run_id}')
def run_detail(run_id: str) -> dict:
    run = _service.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail='run not found')
    return {'status': 'ok', 'item': run}


@router.get('/status')
def runtime_status() -> dict:
    latest_run = next(iter(_service.list_runs(limit=1)), None)
    latest_position = CONTAINER.runtime_store.fetchone_dict(
        '''
        SELECT run_id, created_at, COUNT(*) AS position_count
        FROM portfolio_positions
        GROUP BY run_id, created_at
        ORDER BY created_at DESC
        LIMIT 1
        '''
    )
    latest_signal = CONTAINER.runtime_store.fetchone_dict(
        '''
        SELECT created_at, COUNT(*) AS signal_count
        FROM signals
        GROUP BY created_at
        ORDER BY created_at DESC
        LIMIT 1
        '''
    )
    latest_exec = CONTAINER.runtime_store.fetchone_dict(
        '''
        SELECT created_at, fill_count, order_count
        FROM execution_quality_snapshots
        ORDER BY created_at DESC
        LIMIT 1
        '''
    )
    trading_state = _service.get_trading_state()
    return {
        'status': 'ok',
        'mock_mode': False,
        'latest_run_id': latest_run.get('run_id') if latest_run else None,
        'latest_run_timestamp': latest_run.get('created_at') if latest_run else None,
        'latest_signal_count': int(latest_signal.get('signal_count', 0) or 0) if latest_signal else 0,
        'latest_position_count': int(latest_position.get('position_count', 0) or 0) if latest_position else 0,
        'latest_execution_timestamp': latest_exec.get('created_at') if latest_exec else None,
        'latest_fill_count': int(latest_exec.get('fill_count', 0) or 0) if latest_exec else 0,
        'alerts': [],
        'trading_state': trading_state.get('trading_state', 'running'),
        'state_note': trading_state.get('note', ''),
        'as_of': latest_run.get('created_at') if latest_run else None,
    }


@router.get('/trading-state')
def trading_state() -> dict:
    return {'status': 'ok', **_service.get_trading_state()}


@router.post('/resume')
def runtime_resume() -> dict:
    state = _service.resume_trading('Runtime resumed', actor='api')
    return {'status': 'ok', **state}


@router.post('/kill-switch')
def runtime_kill_switch() -> dict:
    state = _service.halt_trading('Kill switch triggered in V12 runtime', actor='api')
    return {'status': 'ok', **state}


@router.post('/pause')
def runtime_pause() -> dict:
    state = _service.set_trading_state('paused', 'Runtime paused')
    cancelled = _service.cancel_open_execution_orders('paused')
    _service._append_execution_halt_snapshot('paused', 'Runtime paused', cancelled)
    state['cancelled_open_orders'] = cancelled
    return {'status': 'ok', **state}
