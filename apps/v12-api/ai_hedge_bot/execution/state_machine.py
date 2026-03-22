from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from ai_hedge_bot.contracts.reason_codes import EXECUTION_DISABLED, RISK_GUARD_BLOCK, STALE_MARKET_DATA

RECENT_ACTIVITY_TTL_SEC = 180.0
STALE_OPEN_ORDER_TTL_SEC = 300.0


@dataclass(slots=True)
class ExecutionStateInput:
    trading_state: str = 'running'
    active_plan_count: int = 0
    expired_plan_count: int = 0
    open_order_count: int = 0
    submitted_order_count: int = 0
    fill_count: int = 0
    planner_age_sec: float | None = None
    execution_age_sec: float | None = None
    last_fill_age_sec: float | None = None
    reasons: tuple[str, ...] = ()


def classify_execution_state(inp: ExecutionStateInput) -> str:
    trading_state = str(inp.trading_state or 'running').lower()
    reasons = {str(x) for x in inp.reasons}
    recent_fill = inp.last_fill_age_sec is not None and inp.last_fill_age_sec <= RECENT_ACTIVITY_TTL_SEC
    has_orders = inp.open_order_count > 0 or inp.submitted_order_count > 0
    stale_orders = has_orders and inp.last_fill_age_sec is not None and inp.last_fill_age_sec > STALE_OPEN_ORDER_TTL_SEC

    if trading_state == 'halted' or reasons & {'risk_halted', 'kill_switch_triggered', EXECUTION_DISABLED}:
        return 'halted'
    if trading_state == 'paused' or reasons & {'paused', 'blocked_by_risk', EXECUTION_DISABLED, RISK_GUARD_BLOCK}:
        return 'blocked'
    if reasons & {'insufficient_margin', 'stale_quote', 'adapter_error', 'simulator_disabled', STALE_MARKET_DATA, RISK_GUARD_BLOCK}:
        return 'blocked'
    if reasons & {'residual_orders_after_halt', 'open_orders_not_draining'}:
        return 'degraded'
    if stale_orders or 'stale_open_orders' in reasons:
        return 'degraded'
    if recent_fill and has_orders:
        return 'partially_filled'
    if recent_fill and inp.fill_count > 0:
        return 'filled'
    if inp.expired_plan_count > 0 and inp.active_plan_count == 0:
        if has_orders:
            return 'degraded'
        return 'expired'
    if has_orders:
        return 'submitted'
    if inp.active_plan_count > 0:
        if inp.execution_age_sec is not None and inp.execution_age_sec > 45:
            return 'degraded'
        return 'planned'
    if inp.planner_age_sec is not None and inp.planner_age_sec <= 20:
        return 'degraded'
    return 'idle'


def default_reason_codes(inp: ExecutionStateInput) -> list[dict]:
    reasons: list[dict] = []
    trading_state = str(inp.trading_state or 'running').lower()
    recent_fill = inp.last_fill_age_sec is not None and inp.last_fill_age_sec <= RECENT_ACTIVITY_TTL_SEC
    has_orders = inp.open_order_count > 0 or inp.submitted_order_count > 0
    stale_orders = has_orders and inp.last_fill_age_sec is not None and inp.last_fill_age_sec > STALE_OPEN_ORDER_TTL_SEC

    if trading_state == 'halted':
        reasons.append({'code': 'risk_halted', 'severity': 'critical', 'message': 'Trading is halted by runtime control state.'})
        reasons.append({'code': 'kill_switch_triggered', 'severity': 'critical', 'message': 'Kill switch or risk halt is active.'})
        if has_orders:
            reasons.append({'code': 'residual_orders_after_halt', 'severity': 'critical', 'message': 'Open or submitted child orders remain after trading halt.'})
            if stale_orders:
                reasons.append({'code': 'open_orders_not_draining', 'severity': 'critical', 'message': 'Residual open orders are not draining after halt.'})
    elif trading_state == 'paused':
        reasons.append({'code': 'paused', 'severity': 'high', 'message': 'Trading is paused by runtime control state.'})
        if has_orders:
            reasons.append({'code': 'blocked_by_risk', 'severity': 'high', 'message': 'Orders remain while trading is paused.'})

    if recent_fill:
        reasons.append({'code': 'recent_execution_activity', 'severity': 'info', 'message': 'Recent fills or execution activity detected.'})
    if has_orders:
        reasons.append({'code': 'working_orders', 'severity': 'medium', 'message': 'There are working child orders in the market.'})
    if inp.active_plan_count > 0 and inp.open_order_count == 0 and inp.fill_count == 0:
        reasons.append({'code': 'planner_no_execution', 'severity': 'high', 'message': 'Planner is active but no child orders or fills were generated.'})
    if inp.submitted_order_count > 0 and inp.fill_count == 0:
        reasons.append({'code': 'no_fill_after_submit', 'severity': 'high', 'message': 'Orders were submitted but no fills arrived.'})
    if inp.expired_plan_count > 0:
        reasons.append({'code': 'expired_plan', 'severity': 'medium', 'message': 'At least one execution plan has expired.'})
    if stale_orders or (inp.expired_plan_count > 0 and inp.active_plan_count == 0 and has_orders):
        reasons.append({'code': 'stale_open_orders', 'severity': 'high', 'message': 'Expired or stale plans still have open or submitted child orders.'})
    for code in inp.reasons:
        if code in {'risk_halted', 'kill_switch_triggered', 'paused', 'blocked_by_risk', 'residual_orders_after_halt', 'open_orders_not_draining', 'recent_execution_activity', 'working_orders', 'planner_no_execution', 'no_fill_after_submit', 'expired_plan', 'stale_open_orders'}:
            continue
        reasons.append({'code': code, 'severity': 'medium', 'message': code.replace('_', ' ')})
    return reasons


def merge_reason_codes(*groups: Iterable[dict]) -> list[dict]:
    seen: set[str] = set()
    merged: list[dict] = []
    for group in groups:
        for item in group:
            code = str(item.get('code') or '')
            if not code or code in seen:
                continue
            seen.add(code)
            merged.append(item)
    return merged
