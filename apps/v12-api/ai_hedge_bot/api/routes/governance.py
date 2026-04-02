from __future__ import annotations

from fastapi import APIRouter

from ai_hedge_bot.app.container import CONTAINER
from ai_hedge_bot.services.governance_runtime_control_service import GovernanceRuntimeControlService

router = APIRouter(prefix='/governance', tags=['governance'])
_runtime_control = GovernanceRuntimeControlService()


@router.get('/budgets')
def governance_budgets() -> list[dict]:
    return CONTAINER.sprint5c_service.get_latest_budgets()


@router.get('/regime')
def governance_regime() -> dict:
    return CONTAINER.sprint5c_service.get_latest_regime()


@router.get('/runtime-control/routing/latest')
def governance_runtime_control_routing_latest() -> dict:
    return _runtime_control.routing_control_latest()


@router.get('/runtime-control/slippage-guard/latest')
def governance_runtime_control_slippage_guard_latest() -> dict:
    return _runtime_control.slippage_guard_latest()


@router.post('/runtime-control/slippage-guard/apply')
def governance_runtime_control_slippage_guard_apply() -> dict:
    return _runtime_control.apply_slippage_guard_latest()


@router.get('/runtime-control/latency-throttle/latest')
def governance_runtime_control_latency_throttle_latest() -> dict:
    return _runtime_control.latency_throttle_latest()


@router.get('/runtime-control/symbol-reallocation/latest')
def governance_runtime_control_symbol_reallocation_latest() -> dict:
    return _runtime_control.symbol_capital_reallocation_latest()


@router.get('/runtime-control/closed-loop/latest')
def governance_runtime_control_closed_loop_latest() -> dict:
    return _runtime_control.closed_loop_adaptive_control_latest()


@router.post('/runtime-control/closed-loop/apply')
def governance_runtime_control_closed_loop_apply() -> dict:
    return _runtime_control.apply_closed_loop_adaptive_control_latest()


@router.get('/runtime-control/policy-arbitration/latest')
def governance_runtime_control_policy_arbitration_latest() -> dict:
    return _runtime_control.cross_control_policy_arbitration_latest()


@router.post('/runtime-control/policy-arbitration/apply')
def governance_runtime_control_policy_arbitration_apply() -> dict:
    return _runtime_control.apply_cross_control_policy_arbitration_latest()
