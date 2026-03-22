from __future__ import annotations

from typing import Any


DEFAULT_BREAKDOWN = {
    'balance': 0.0,
    'used_margin': 0.0,
    'unrealized': 0.0,
    'free_margin': 0.0,
    'total_equity': 0.0,
}


def _to_float(value: Any, fallback: float = 0.0) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return fallback
    return number if number == number else fallback



def _extract_summary(payload: dict | None) -> dict:
    if not isinstance(payload, dict):
        return {}
    summary = payload.get('summary')
    return summary if isinstance(summary, dict) else payload



def _extract_positions(payload: dict | None) -> list[dict]:
    if not isinstance(payload, dict):
        return []
    items = payload.get('items') or payload.get('positions') or []
    return [row for row in items if isinstance(row, dict)]



def _first_of(row: dict[str, Any], *keys: str, default: Any = 0.0) -> Any:
    for key in keys:
        if key in row and row.get(key) is not None:
            return row.get(key)
    return default



def _rounded_breakdown(balance: float, used_margin: float, unrealized: float, total_equity: float | None = None) -> dict:
    computed_total_equity = balance + unrealized if total_equity is None else total_equity
    free_margin = computed_total_equity - used_margin
    total_equity = computed_total_equity
    return {
        'balance': round(balance, 2),
        'used_margin': round(used_margin, 2),
        'unrealized': round(unrealized, 2),
        'free_margin': round(free_margin, 2),
        'total_equity': round(total_equity, 2),
    }



def compute_equity_breakdown(portfolio_dashboard_payload: dict | None, portfolio_positions_payload: dict | None = None) -> dict:
    summary = _extract_summary(portfolio_dashboard_payload)
    positions = _extract_positions(portfolio_positions_payload)

    balance = _to_float(
        _first_of(summary, 'balance', 'cash_balance', 'cash', 'free_cash', default=0.0),
        0.0,
    )
    total_equity = _to_float(_first_of(summary, 'total_equity', 'portfolio_value', default=balance), balance)
    used_margin = 0.0
    unrealized = 0.0
    market_value = 0.0
    for row in positions:
        qty_raw = _first_of(row, 'signed_qty', 'quantity', 'qty', 'position_qty', default=0.0)
        avg_raw = _first_of(row, 'avg_price', 'avg_entry_price', 'avg', default=0.0)
        mark_raw = _first_of(row, 'mark_price', 'markPrice', 'price', 'last_price', default=avg_raw)
        pnl_raw = _first_of(row, 'pnl', 'unrealized_pnl', 'unrealized', default=0.0)
        signed_qty = _to_float(qty_raw, 0.0)
        qty = abs(signed_qty)
        avg = abs(_to_float(avg_raw, 0.0))
        mark = _to_float(mark_raw, avg)
        pnl = _to_float(pnl_raw, 0.0)
        used_margin += qty * avg
        unrealized += pnl
        market_value += signed_qty * mark

    if not positions:
        used_margin = _to_float(_first_of(summary, 'used_margin', default=0.0), 0.0)
        unrealized = _to_float(_first_of(summary, 'unrealized_pnl', 'unrealized', default=0.0), 0.0)
        market_value = _to_float(_first_of(summary, 'market_value', default=0.0), 0.0)

    if total_equity == balance and positions:
        total_equity = balance + _to_float(_first_of(summary, 'market_value', default=market_value), market_value)
        if total_equity == balance:
            total_equity = balance + unrealized

    return _rounded_breakdown(balance, used_margin, unrealized, total_equity=total_equity)
