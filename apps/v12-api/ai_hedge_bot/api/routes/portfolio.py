from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter
from ai_hedge_bot.app.container import CONTAINER
from ai_hedge_bot.signal.signal_service import SignalService
from ai_hedge_bot.portfolio.portfolio_service_phaseg import PhaseGPortfolioService
from ai_hedge_bot.data.storage.jsonl_logger import JsonlLogger
from ai_hedge_bot.core.clock import utc_now_iso
from ai_hedge_bot.core.ids import new_cycle_id, new_signal_id
from ai_hedge_bot.repositories.sprint5_repository import Sprint5Repository
from ai_hedge_bot.api.routes.execution import _get_execution_quality_latest_summary

router = APIRouter(prefix='/portfolio', tags=['portfolio'])
_signal_service = SignalService()
_portfolio_service = PhaseGPortfolioService()
_decision_logger = JsonlLogger(CONTAINER.runtime_dir / 'logs' / 'portfolio_weights.jsonl')
_diag_logger = JsonlLogger(CONTAINER.runtime_dir / 'logs' / 'portfolio_diagnostics.jsonl')
_repo = Sprint5Repository()
PORTFOLIO_EQUITY_HISTORY_CACHE_TTL_SECONDS = 5.0
_equity_history_cache: dict[tuple[int], dict[str, object]] = {}
PORTFOLIO_METRICS_CACHE_TTL_SECONDS = 5.0
_portfolio_metrics_cache: dict[str, object] = {'expires_at': None, 'payload': None}
PORTFOLIO_DIAGNOSTICS_CACHE_TTL_SECONDS = 5.0
_portfolio_diagnostics_cache: dict[str, object] = {'expires_at': None, 'payload': None}
PORTFOLIO_POSITIONS_CACHE_TTL_SECONDS = 3.0
_portfolio_positions_cache: dict[str, object] = {'expires_at': None, 'payload': None}


def _build_equity_history_payload(limit: int) -> dict:
    rows = CONTAINER.runtime_store.fetchall_dict(
        """
        SELECT snapshot_time, total_equity, unrealized_pnl + realized_pnl AS pnl, drawdown
        FROM equity_snapshots
        ORDER BY snapshot_time DESC
        LIMIT ?
        """,
        [limit],
    )
    items = [
        {
            'name': str(row.get('snapshot_time')),
            'value': float(row.get('total_equity', 0.0) or 0.0),
            'pnl': float(row.get('pnl', 0.0) or 0.0),
            'drawdown': float(row.get('drawdown', 0.0) or 0.0),
            'as_of': str(row.get('snapshot_time')),
        }
        for row in reversed(rows)
    ]
    return {'status': 'ok', 'items': items, 'as_of': items[-1]['as_of'] if items else None}


def _safe_expected_sharpe_from_equity_history(items: list[dict]) -> float | None:
    if len(items) < 3:
        return 0.0 if items else None
    returns: list[float] = []
    prev = None
    for item in items:
        value = float(item.get('value', 0.0) or 0.0)
        if prev and abs(prev) > 1e-9:
            returns.append((value - prev) / abs(prev))
        prev = value
    if len(returns) < 2:
        return 0.0
    mean_ret = sum(returns) / len(returns)
    variance = sum((r - mean_ret) ** 2 for r in returns) / max(len(returns) - 1, 1)
    std = variance ** 0.5
    if std < 1e-6:
        return 0.0
    return round(max(-10.0, min(10.0, mean_ret / std)), 6)


def _build_portfolio_metrics_payload(limit: int = 60) -> dict:
    quality = _get_execution_quality_latest_summary()
    equity_history = _build_equity_history_payload(limit)
    equity_items = equity_history.get('items') or []
    if not isinstance(equity_items, list):
        equity_items = []
    returns: list[float] = []
    prev = None
    for item in equity_items:
        value = float(item.get('value', 0.0) or 0.0)
        if prev and abs(prev) > 1e-9:
            returns.append((value - prev) / abs(prev))
        prev = value
    expected_volatility = 0.0
    if returns:
        mean_ret = sum(returns) / len(returns)
        variance = sum((r - mean_ret) ** 2 for r in returns) / max(len(returns) - 1, 1)
        expected_volatility = round(variance ** 0.5, 6)
    return {
        'status': 'ok',
        'fill_rate': float(quality.get('fill_rate', 0.0) or 0.0),
        'expected_sharpe': _safe_expected_sharpe_from_equity_history(equity_items),
        'expected_volatility': expected_volatility,
        'source_snapshot_time': quality.get('as_of') or equity_history.get('as_of'),
        'as_of': quality.get('as_of') or equity_history.get('as_of'),
        'build_status': 'live',
        'equity_history_limit': int(limit),
    }


def _decorate_cached_payload(payload: dict, *, build_status: str) -> dict:
    result = dict(payload)
    source_snapshot_time = result.get('source_snapshot_time') or result.get('as_of')
    result['source_snapshot_time'] = source_snapshot_time
    if build_status:
        result['build_status'] = build_status
    return result


def _load_latest_signals() -> list[dict]:
    rows = CONTAINER.runtime_store.fetchall_dict(
        """
        SELECT signal_id, symbol, side, score, dominant_alpha, alpha_family, horizon,
               turnover_profile, regime, metadata_json
        FROM signals
        WHERE created_at = (SELECT MAX(created_at) FROM signals)
        ORDER BY symbol
        """
    )
    if not rows:
        return _signal_service.generate(CONTAINER.config.symbols)
    return [
        {
            'signal_id': r['signal_id'],
            'symbol': r['symbol'],
            'side': r['side'],
            'score': r['score'],
            'dominant_alpha': r['dominant_alpha'],
            'alpha_family': r['alpha_family'],
            'horizon': r['horizon'],
            'turnover_profile': r['turnover_profile'],
            'regime': r['regime'],
            'metadata': {},
        }
        for r in rows
    ]


@router.post('/prepare')
def prepare_portfolio() -> dict:
    signals = _load_latest_signals()
    result = _portfolio_service.prepare(signals)
    created_at = utc_now_iso()
    diag_row = {
        'diagnostics_id': new_cycle_id(),
        'created_at': created_at,
        'input_signals': result['diagnostics']['input_signals'],
        'kept_signals': result['diagnostics']['kept_signals'],
        'crowding_flags_json': CONTAINER.runtime_store.to_json(result['diagnostics']['crowding_flags']),
        'overlap_penalty_applied': result['diagnostics']['overlap_penalty_applied'],
    }
    CONTAINER.runtime_store.append('portfolio_diagnostics', diag_row)
    _diag_logger.append(diag_row)

    decision_rows = []
    for decision in result['decisions']:
        row = {
            'decision_id': new_signal_id(),
            'signal_id': decision['signal_id'],
            'created_at': created_at,
            'symbol': decision['symbol'],
            'side': decision['side'],
            'target_weight': float(decision['target_weight']),
        }
        decision_rows.append(row)
        _decision_logger.append(row)
    CONTAINER.runtime_store.append('portfolio_signal_decisions', decision_rows)
    CONTAINER.latest_portfolio_diagnostics = result['diagnostics']
    return {'status': 'ok', **result}


@router.get('/diagnostics/latest')
def portfolio_diagnostics_latest() -> dict:
    now = datetime.now(timezone.utc)
    expires_at = _portfolio_diagnostics_cache.get('expires_at')
    payload = _portfolio_diagnostics_cache.get('payload')
    if isinstance(expires_at, datetime) and isinstance(payload, dict) and expires_at > now:
        return _decorate_cached_payload(payload, build_status='fresh_cache')
    diagnostics = CONTAINER.latest_portfolio_diagnostics or {
        'input_signals': 0,
        'kept_signals': 0,
        'crowding_flags': [],
        'overlap_penalty_applied': False,
    }
    built = {'status': 'ok', 'diagnostics': diagnostics, 'as_of': utc_now_iso(), 'source_snapshot_time': utc_now_iso(), 'build_status': 'live'}
    _portfolio_diagnostics_cache['expires_at'] = now + timedelta(seconds=PORTFOLIO_DIAGNOSTICS_CACHE_TTL_SECONDS)
    _portfolio_diagnostics_cache['payload'] = dict(built)
    return built


@router.get('/overview')
def portfolio_overview() -> dict:
    payload = _repo.latest_portfolio_overview()
    summary = payload.get('summary') or {}
    return {
        'status': 'ok',
        'total_equity': float(summary.get('total_equity', 0.0) or 0.0),
        'cash_balance': float(summary.get('cash_balance', 0.0) or 0.0),
        'free_cash': float(summary.get('free_cash', summary.get('cash_balance', 0.0)) or 0.0),
        'used_margin': float(summary.get('used_margin', 0.0) or 0.0),
        'collateral_equity': float(summary.get('collateral_equity', float(summary.get('free_cash', summary.get('cash_balance', 0.0)) or 0.0) + float(summary.get('used_margin', 0.0) or 0.0)) or 0.0),
        'available_margin': float(summary.get('available_margin', 0.0) or 0.0),
        'margin_utilization': float(summary.get('margin_utilization', 0.0) or 0.0),
        'gross_exposure': float(summary.get('gross_exposure', 0.0) or 0.0),
        'net_exposure': float(summary.get('net_exposure', 0.0) or 0.0),
        'realized_pnl': float(summary.get('realized_pnl', 0.0) or 0.0),
        'unrealized_pnl': float(summary.get('unrealized_pnl', 0.0) or 0.0),
        'fees_paid': float(summary.get('fees_paid', 0.0) or 0.0),
        'drawdown': float(summary.get('drawdown', 0.0) or 0.0),
        'quotes_as_of': summary.get('quotes_as_of'),
        'stale_positions': int(summary.get('stale_positions', 0) or 0),
        'positions': payload.get('positions', []),
        'snapshot': payload.get('snapshot'),
        'as_of': summary.get('as_of') or (payload.get('snapshot') or {}).get('created_at'),
    }


@router.get('/overview-summary/latest')
def portfolio_overview_summary_latest() -> dict:
    payload = _repo.latest_portfolio_overview_summary()
    summary = payload.get('summary') or {}
    snapshot = payload.get('snapshot') or {}
    return {
        'status': 'ok',
        'summary': summary,
        'snapshot': snapshot,
        'positions': [],
        'as_of': summary.get('as_of') or snapshot.get('created_at'),
    }


@router.get('/metrics/latest')
def portfolio_metrics_latest(limit: int = 60) -> dict:
    now = datetime.now(timezone.utc)
    expires_at = _portfolio_metrics_cache.get('expires_at')
    payload = _portfolio_metrics_cache.get('payload')
    if isinstance(expires_at, datetime) and isinstance(payload, dict) and expires_at > now:
        cached_payload = dict(payload)
        cached_payload['build_status'] = 'fresh_cache'
        return cached_payload
    built = _build_portfolio_metrics_payload(int(limit))
    _portfolio_metrics_cache['expires_at'] = now + timedelta(seconds=PORTFOLIO_METRICS_CACHE_TTL_SECONDS)
    _portfolio_metrics_cache['payload'] = dict(built)
    return built


def _build_portfolio_positions_payload() -> dict:
    overview = _repo.latest_portfolio_overview()
    summary = overview.get('summary') or {}
    positions = []
    equity_denom = max(abs(float(summary.get('total_equity', 0.0) or 0.0)), 1e-9)
    for row in overview.get('positions', []):
        side = row.get('side', 'long')
        sign = 1.0 if side == 'long' else -1.0
        notional = round(float(row.get('exposure_notional', 0.0) or 0.0), 2)
        weight = sign * (notional / equity_denom)
        positions.append(
            {
                'symbol': row.get('symbol'),
                'side': side,
                'weight': weight,
                'target_weight': weight,
                'notional': notional,
                'notional_usd': notional,
                'pnl': float(row.get('unrealized_pnl', 0.0) or 0.0),
                'qty': float(row.get('abs_qty', 0.0) or 0.0),
                'quantity': float(row.get('abs_qty', 0.0) or 0.0),
                'avg_price': float(row.get('avg_entry_price', 0.0) or 0.0),
                'mark_price': float(row.get('mark_price', 0.0) or 0.0),
                'strategy_id': row.get('strategy_id'),
                'alpha_family': row.get('alpha_family') or '',
                'price_source': row.get('price_source'),
                'quote_time': row.get('quote_time'),
                'quote_age_sec': float(row.get('quote_age_sec', 0.0) or 0.0),
                'stale': bool(row.get('stale', False)),
                'timestamp': row.get('updated_at') or summary.get('as_of'),
            }
        )
    return {
        'status': 'ok',
        'run_id': (overview.get('snapshot') or {}).get('run_id'),
        'as_of': summary.get('as_of') or (overview.get('snapshot') or {}).get('created_at'),
        'source_snapshot_time': summary.get('as_of') or (overview.get('snapshot') or {}).get('created_at'),
        'total_equity': float(summary.get('total_equity', 0.0) or 0.0),
        'items': positions,
        'build_status': 'live',
    }


@router.get('/positions/latest')
def portfolio_positions_latest() -> dict:
    now = datetime.now(timezone.utc)
    expires_at = _portfolio_positions_cache.get('expires_at')
    payload = _portfolio_positions_cache.get('payload')
    if isinstance(expires_at, datetime) and isinstance(payload, dict) and expires_at > now:
        return _decorate_cached_payload(payload, build_status='fresh_cache')
    built = _build_portfolio_positions_payload()
    _portfolio_positions_cache['expires_at'] = now + timedelta(seconds=PORTFOLIO_POSITIONS_CACHE_TTL_SECONDS)
    _portfolio_positions_cache['payload'] = dict(built)
    return built


@router.get('/equity-history')
def equity_history(limit: int = 200) -> dict:
    cache_key = (int(limit),)
    now = datetime.now(timezone.utc)
    cached_entry = _equity_history_cache.get(cache_key)
    if cached_entry:
        expires_at = cached_entry.get('expires_at')
        payload = cached_entry.get('payload')
        if isinstance(expires_at, datetime) and payload and expires_at > now:
            return payload  # type: ignore[return-value]
    payload = _build_equity_history_payload(int(limit))
    _equity_history_cache[cache_key] = {
        'expires_at': now + timedelta(seconds=PORTFOLIO_EQUITY_HISTORY_CACHE_TTL_SECONDS),
        'payload': payload,
    }
    return payload


@router.get('/equity-history/live')
def equity_history_live(limit: int = 200) -> dict:
    return _build_equity_history_payload(int(limit))
