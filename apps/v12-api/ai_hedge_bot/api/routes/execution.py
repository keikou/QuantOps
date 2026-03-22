from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter
from ai_hedge_bot.repositories.sprint5_repository import Sprint5Repository
from ai_hedge_bot.services.runtime.runtime_service import RuntimeService
from ai_hedge_bot.services.truth_engine import TruthEngine
from ai_hedge_bot.execution.state_machine import ExecutionStateInput, classify_execution_state, default_reason_codes, merge_reason_codes

router = APIRouter(prefix='/execution', tags=['execution'])
_repo = Sprint5Repository()
_runtime = RuntimeService()
_truth = TruthEngine()


def _parse_ts(value) -> datetime | None:
    if value is None or value == '':
        return None
    try:
        if isinstance(value, datetime):
            dt = value
        else:
            dt = datetime.fromisoformat(str(value).replace('Z', '+00:00'))
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None


def _plan_status(item: dict) -> str:
    metadata = item.get('metadata') or {}
    created_at = _parse_ts(item.get('created_at'))
    if not created_at:
        return str(item.get('status') or 'planned')
    now = datetime.now(timezone.utc)
    age = max(0.0, (now - created_at).total_seconds())
    expire_seconds = int(metadata.get('expire_seconds') or item.get('expire_seconds') or 0)
    decision_price = float(metadata.get('decision_price') or metadata.get('expiry_policy', {}).get('decision_price') or item.get('limit_price') or 0.0)
    drift_bps = float(metadata.get('price_drift_bps') or metadata.get('expiry_policy', {}).get('price_drift_bps') or 0.0)
    latest = _truth.get_latest_market_prices(symbols=[str(item.get('symbol') or '')]).get(str(item.get('symbol') or ''), {})
    mid = float(latest.get('mid') or latest.get('mark_price') or decision_price or 0.0)
    price_drift = abs(mid - decision_price) / max(decision_price, 1e-9) * 10000.0 if decision_price else 0.0
    if expire_seconds and age > expire_seconds:
        return 'expired_time'
    if drift_bps and price_drift > drift_bps:
        return 'expired_price'
    return str(item.get('status') or 'planned')


def _latest_ts_from_rows(rows: list[dict[str, Any]], *keys: str) -> datetime | None:
    latest: datetime | None = None
    for row in rows:
        for key in keys:
            candidate = _parse_ts(row.get(key))
            if candidate and (latest is None or candidate > latest):
                latest = candidate
    return latest


def _enrich_plan_activity(items: list[dict], orders: list[dict], fills: list[dict], trading_state: str = 'running') -> tuple[list[dict], int, int]:
    now = datetime.now(timezone.utc)
    orders_by_plan: dict[str, list[dict[str, Any]]] = {}
    fills_by_plan: dict[str, list[dict[str, Any]]] = {}
    for row in orders:
        plan_id = str(row.get('plan_id') or row.get('planId') or '')
        if plan_id:
            orders_by_plan.setdefault(plan_id, []).append(row)
    for row in fills:
        plan_id = str(row.get('plan_id') or row.get('planId') or '')
        if plan_id:
            fills_by_plan.setdefault(plan_id, []).append(row)

    active_count = 0
    visible_count = 0
    state_name = str(trading_state or 'running').lower()
    for item in items:
        plan_id = str(item.get('plan_id') or item.get('planId') or '')
        plan_orders = orders_by_plan.get(plan_id, [])
        plan_fills = fills_by_plan.get(plan_id, [])
        created_at = _parse_ts(item.get('created_at'))
        latest_order_at = _latest_ts_from_rows(plan_orders, 'submit_time', 'updated_at', 'created_at')
        latest_fill_at = _latest_ts_from_rows(plan_fills, 'created_at', 'event_time')
        latest_activity_at = max([dt for dt in [latest_order_at, latest_fill_at] if dt is not None], default=None)
        has_open_orders = any(str(row.get('status') or '').lower() in {'submitted', 'partially_filled', 'open'} for row in plan_orders)
        recently_executed = False
        if latest_activity_at is not None:
            recently_executed = max(0.0, (now - latest_activity_at).total_seconds()) <= 120.0
        item['created_at'] = created_at.isoformat() if created_at else item.get('created_at')
        item['plan_age_sec'] = round(max(0.0, (now - created_at).total_seconds()), 3) if created_at else None
        item['last_execution_at'] = latest_activity_at.isoformat() if latest_activity_at else None
        item['last_execution_age_sec'] = round(max(0.0, (now - latest_activity_at).total_seconds()), 3) if latest_activity_at else None
        item['has_open_orders'] = has_open_orders
        item['order_count'] = len(plan_orders)
        item['fill_count'] = len(plan_fills)
        item['active'] = bool(has_open_orders or recently_executed)
        item['activity_state'] = 'executing' if has_open_orders else ('recent_fill' if recently_executed else 'planned_only')
        if state_name in {'halted', 'paused'}:
            if has_open_orders:
                item['active'] = False
                item['activity_state'] = 'residual_orders_after_halt' if state_name == 'halted' else 'blocked_by_risk'
            elif recently_executed:
                item['active'] = False
                item['activity_state'] = 'recent_fill_before_halt'
            else:
                item['active'] = False
                item['activity_state'] = 'halted'
        if item.get('effective_status') and str(item['effective_status']).startswith('expired'):
            item['active'] = False
            item['activity_state'] = 'expired'
        if not str(item.get('effective_status') or '').startswith('expired'):
            visible_count += 1
        if item['active']:
            active_count += 1
    return items, active_count, visible_count


@router.get('/quality/latest')
def execution_quality_latest() -> dict:
    return _repo.latest_execution_quality()


@router.get('/fills')
def execution_fills(limit: int = 100) -> dict:
    items = _repo.store.fetchall_dict(
        """
        SELECT fill_id, created_at, run_id, mode, plan_id, order_id, client_order_id, strategy_id, alpha_family,
               symbol, side, fill_qty, fill_price, slippage_bps, latency_ms, fee_bps,
               bid, ask, arrival_mid_price, price_source, quote_time, quote_age_sec, fallback_reason, status
        FROM execution_fills
        ORDER BY created_at DESC, symbol ASC
        LIMIT ?
        """,
        [limit],
    )
    return {'status': 'ok', 'items': items, 'as_of': items[0].get('created_at') if items else None, 'run_id': items[0].get('run_id') if items else None}


@router.get('/plans')
def execution_plans(limit: int = 100) -> dict:
    items = _repo.store.fetchall_dict(
        """
        SELECT plan_id, created_at, run_id, mode, symbol, side, target_weight, order_qty, limit_price,
               participation_rate, status, algo, route, expire_seconds, slice_count, metadata_json
        FROM execution_plans
        ORDER BY created_at DESC, symbol ASC
        LIMIT ?
        """,
        [limit],
    )
    active_count = 0
    expired_count = 0
    for item in items:
        if item.get('metadata_json'):
            try:
                item['metadata'] = json.loads(item['metadata_json'])
            except Exception:
                item['metadata'] = {}
        item['created_at'] = _parse_ts(item.get('created_at')).isoformat() if _parse_ts(item.get('created_at')) else item.get('created_at')
        effective_status = _plan_status(item)
        item['effective_status'] = effective_status
        if effective_status.startswith('expired'):
            expired_count += 1
        else:
            active_count += 1
    trading_state = _runtime.get_trading_state().get('trading_state', 'running')
    return {
        'status': 'ok',
        'items': items,
        'active_count': active_count,
        'expired_count': expired_count,
        'trading_state': trading_state,
        'as_of': items[0].get('created_at') if items else None,
        'run_id': items[0].get('run_id') if items else None,
    }


@router.get('/planner/latest')
def execution_planner_latest() -> dict:
    plans = execution_plans(limit=20)
    orders_payload = execution_orders(limit=500)
    fills_payload = execution_fills(limit=500)
    items = plans.get('items', [])
    enriched_items, active_count, visible_count = _enrich_plan_activity(items, orders_payload.get('items', []), fills_payload.get('items', []), trading_state=plans.get('trading_state', 'running'))
    visible_items = [item for item in enriched_items if not str(item.get('effective_status', '')).startswith('expired')]
    algo_mix = {}
    route_mix = {}
    for item in visible_items:
        algo_mix[item.get('algo') or 'unknown'] = algo_mix.get(item.get('algo') or 'unknown', 0) + 1
        route_mix[item.get('route') or 'unknown'] = route_mix.get(item.get('route') or 'unknown', 0) + 1
    newest_activity = _latest_ts_from_rows(enriched_items, 'last_execution_at', 'created_at')
    return {
        'status': 'ok',
        'trading_state': plans.get('trading_state', 'running'),
        'plan_count': active_count,
        'visible_plan_count': visible_count,
        'expired_count': int(plans.get('expired_count', 0) or 0),
        'algo_mix': algo_mix,
        'route_mix': route_mix,
        'items': visible_items[:5],
        'as_of': plans.get('as_of'),
        'latest_activity_at': newest_activity.isoformat() if newest_activity else None,
    }


@router.get('/orders')
def execution_orders(limit: int = 100) -> dict:
    items = _repo.store.fetchall_dict(
        """
        SELECT order_id, plan_id, parent_order_id, client_order_id, strategy_id, alpha_family,
               symbol, side, order_type, qty, limit_price, venue, route, algo, submit_time,
               status, source, metadata_json, created_at, updated_at
        FROM execution_orders
        ORDER BY COALESCE(submit_time, created_at) DESC, symbol ASC
        LIMIT ?
        """,
        [limit],
    )
    for item in items:
        if item.get('metadata_json'):
            try:
                item['metadata'] = json.loads(item['metadata_json'])
            except Exception:
                item['metadata'] = {}
    return {'status': 'ok', 'items': items, 'as_of': items[0].get('submit_time') if items else None}


@router.get('/orders/latest')
def execution_orders_latest(limit: int = 25) -> dict:
    return execution_orders(limit=limit)


def _latest_execution_state_payload() -> dict:
    trading_state = _runtime.get_trading_state().get('trading_state', 'running')
    plans = execution_plans(limit=200)
    orders_payload = execution_orders(limit=500)
    fills_payload = execution_fills(limit=500)
    expired_plan_count = int(plans.get('expired_count', 0) or 0)
    orders = orders_payload.get('items', [])
    fills = fills_payload.get('items', [])
    _, active_plan_count, visible_plan_count = _enrich_plan_activity(plans.get('items', []), orders, fills, trading_state=str(trading_state))
    open_order_count = sum(1 for row in orders if str(row.get('status') or '').lower() in {'submitted', 'partially_filled', 'open'})
    submitted_order_count = sum(1 for row in orders if str(row.get('status') or '').lower() not in {'cancelled', 'rejected'})
    state_name = str(trading_state or 'running').lower()
    latest_plan_at = _parse_ts(plans.get('as_of'))
    latest_order_at = _parse_ts(orders_payload.get('as_of'))
    latest_fill_at = _parse_ts(fills_payload.get('as_of'))
    now = datetime.now(timezone.utc)
    planner_age_sec = max(0.0, (now - latest_plan_at).total_seconds()) if latest_plan_at else None
    execution_age_sec = max(0.0, (now - latest_order_at).total_seconds()) if latest_order_at else None
    last_fill_age_sec = max(0.0, (now - latest_fill_at).total_seconds()) if latest_fill_at else None
    manual_reasons: list[dict] = []
    recent_execution_activity = last_fill_age_sec is not None and last_fill_age_sec <= 180.0
    stale_open_orders = (open_order_count > 0 or submitted_order_count > 0) and (last_fill_age_sec is None or last_fill_age_sec > 300.0)
    if state_name == 'halted':
        manual_reasons.append({'code': 'risk_halted', 'severity': 'critical', 'message': 'Trading is halted by runtime control state.'})
        manual_reasons.append({'code': 'kill_switch_triggered', 'severity': 'critical', 'message': 'Kill switch or risk halt is active.'})
        if open_order_count > 0 or submitted_order_count > 0:
            manual_reasons.append({'code': 'residual_orders_after_halt', 'severity': 'critical', 'message': 'Orders remain after halt and must drain/cancel.'})
            if stale_open_orders:
                manual_reasons.append({'code': 'open_orders_not_draining', 'severity': 'critical', 'message': 'Open orders remain after halt without recent fills.'})
    elif state_name == 'paused':
        manual_reasons.append({'code': 'paused', 'severity': 'high', 'message': 'Trading is paused by runtime control state.'})
        if open_order_count > 0 or submitted_order_count > 0:
            manual_reasons.append({'code': 'blocked_by_risk', 'severity': 'high', 'message': 'Orders remain while trading is paused.'})
    if active_plan_count > 0 and submitted_order_count == 0 and len(fills) == 0 and state_name == 'running':
        manual_reasons.append({'code': 'planner_no_execution', 'severity': 'high', 'message': 'Planner is active but no orders or fills exist.'})
    if submitted_order_count > 0 and len(fills) == 0 and state_name == 'running':
        manual_reasons.append({'code': 'no_fill_after_submit', 'severity': 'high', 'message': 'Orders exist but no fills were recorded.'})
    if recent_execution_activity and state_name == 'running':
        manual_reasons.append({'code': 'recent_execution_activity', 'severity': 'info', 'message': 'Recent fills or execution activity detected.'})
    if (open_order_count > 0 or submitted_order_count > 0) and state_name == 'running':
        manual_reasons.append({'code': 'working_orders', 'severity': 'medium', 'message': 'Orders are still working in the market.'})
    if stale_open_orders:
        manual_reasons.append({'code': 'stale_open_orders', 'severity': 'high', 'message': 'Open orders remain without recent fills.'})
    inp = ExecutionStateInput(
        trading_state=str(trading_state),
        active_plan_count=active_plan_count,
        expired_plan_count=expired_plan_count,
        open_order_count=open_order_count,
        submitted_order_count=submitted_order_count,
        fill_count=len(fills),
        planner_age_sec=planner_age_sec,
        execution_age_sec=execution_age_sec,
        last_fill_age_sec=last_fill_age_sec,
        reasons=tuple(str(item.get('code') or '') for item in manual_reasons),
    )
    reasons = merge_reason_codes(manual_reasons, default_reason_codes(inp))
    priority = ['risk_halted', 'kill_switch_triggered', 'blocked_by_risk', 'paused', 'residual_orders_after_halt', 'open_orders_not_draining', 'stale_open_orders', 'working_orders', 'recent_execution_activity', 'planner_no_execution', 'no_fill_after_submit', 'expired_plan']
    reason = None
    for code in priority:
        if any(str(item.get('code')) == code for item in reasons):
            reason = code
            break
    if reason is None and reasons:
        reason = reasons[0]['code']
    execution_state = classify_execution_state(inp)
    return {
        'status': 'ok',
        'trading_state': trading_state,
        'execution_state': execution_state,
        'reason': reason,
        'planner_age_sec': planner_age_sec,
        'execution_age_sec': execution_age_sec,
        'last_fill_age_sec': last_fill_age_sec,
        'open_order_count': open_order_count,
        'submitted_order_count': submitted_order_count,
        'active_plan_count': active_plan_count,
        'expired_plan_count': expired_plan_count,
        'visible_plan_count': visible_plan_count,
        'latest_plan_id': None if state_name in {'halted', 'paused'} else ((plans.get('items') or [{}])[0].get('plan_id') if plans.get('items') else None),
        'latest_order_id': None if state_name in {'halted', 'paused'} else (orders[0].get('order_id') if orders else None),
        'latest_fill_id': fills[0].get('fill_id') if fills else None,
        'block_reasons': reasons,
        'as_of': fills_payload.get('as_of') or orders_payload.get('as_of') or plans.get('as_of'),
    }


@router.get('/state/latest')
def execution_state_latest() -> dict:
    payload = _latest_execution_state_payload()
    CONTAINER = None
    try:
        from ai_hedge_bot.app.container import CONTAINER as _CONTAINER
        CONTAINER = _CONTAINER
        _CONTAINER.runtime_store.append('execution_state_snapshots', {
            'as_of': payload.get('as_of') or datetime.now(timezone.utc).isoformat(),
            'trading_state': payload.get('trading_state'),
            'execution_state': payload.get('execution_state'),
            'reason': payload.get('reason'),
            'planner_age_sec': payload.get('planner_age_sec'),
            'execution_age_sec': payload.get('execution_age_sec'),
            'last_fill_age_sec': payload.get('last_fill_age_sec'),
            'open_order_count': payload.get('open_order_count'),
            'active_plan_count': payload.get('active_plan_count'),
            'expired_plan_count': payload.get('expired_plan_count'),
            'latest_plan_id': payload.get('latest_plan_id'),
            'latest_order_id': payload.get('latest_order_id'),
            'latest_fill_id': payload.get('latest_fill_id'),
        })
    except Exception:
        pass
    return payload


@router.get('/block-reasons/latest')
def execution_block_reasons_latest() -> dict:
    payload = _latest_execution_state_payload()
    return {'status': 'ok', 'items': payload.get('block_reasons', []), 'as_of': payload.get('as_of')}
