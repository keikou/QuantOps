from __future__ import annotations

from datetime import datetime, timezone
from datetime import timedelta

from fastapi import APIRouter
from pydantic import BaseModel

from ai_hedge_bot.strategy.strategy_service import StrategyService
from ai_hedge_bot.repositories.sprint5_repository import Sprint5Repository

router = APIRouter(prefix='/strategy', tags=['strategy'])
_service = StrategyService()
_repo = Sprint5Repository()
_lifecycle_state: dict[str, dict] = {}
_risk_budget_cache: dict[str, object | None] = {"expires_at": None, "payload": None}
_RISK_BUDGET_TTL_SECONDS = 5.0


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class StrategyLifecycleBody(BaseModel):
    strategy_id: str | None = None
    note: str | None = None


def _apply_lifecycle(strategy_id: str, desired_state: str, note: str | None = None) -> dict:
    item = {
        'strategy_id': strategy_id,
        'status': desired_state,
        'accepted': True,
        'note': note,
        'as_of': _now(),
    }
    _lifecycle_state[strategy_id] = item
    return {'status': 'ok', 'strategy_id': strategy_id, 'desired_state': desired_state, 'runtime_state': item, 'as_of': item['as_of']}


@router.get('/registry')
def registry() -> dict:
    payload = _service.registry_view()
    strategies = payload.get('strategies') or payload.get('items') or []
    for row in strategies:
        sid = row.get('strategy_id')
        if sid in _lifecycle_state:
            row['runtime_state'] = _lifecycle_state[sid]
    return payload


@router.post('/allocate-capital')
def allocate_capital() -> dict:
    return _service.allocate_capital()


@router.get('/risk-budget')
def risk_budget() -> dict:
    now = datetime.now(timezone.utc)
    expires_at = _risk_budget_cache.get("expires_at")
    payload = _risk_budget_cache.get("payload")
    if isinstance(expires_at, datetime) and expires_at > now and isinstance(payload, dict):
        cached = dict(payload)
        cached["build_status"] = "fresh_cache"
        return cached
    live = dict(_service.latest_risk_budget())
    live["build_status"] = "live"
    _risk_budget_cache["payload"] = dict(live)
    _risk_budget_cache["expires_at"] = now + timedelta(seconds=_RISK_BUDGET_TTL_SECONDS)
    return live


@router.get('/signals/latest')
def latest_signals() -> dict:
    return _repo.latest_signal_snapshot()


@router.post('/{strategy_id}/start')
def start_strategy(strategy_id: str, body: StrategyLifecycleBody | None = None) -> dict:
    return _apply_lifecycle(strategy_id, 'running', body.note if body else None)


@router.post('/{strategy_id}/stop')
def stop_strategy(strategy_id: str, body: StrategyLifecycleBody | None = None) -> dict:
    return _apply_lifecycle(strategy_id, 'stopped', body.note if body else None)


@router.post('/{strategy_id}/pause')
def pause_strategy(strategy_id: str, body: StrategyLifecycleBody | None = None) -> dict:
    return _apply_lifecycle(strategy_id, 'paused', body.note if body else None)


@router.post('/{strategy_id}/reload')
def reload_strategy(strategy_id: str, body: StrategyLifecycleBody | None = None) -> dict:
    return _apply_lifecycle(strategy_id, 'reloading', body.note if body else None)
