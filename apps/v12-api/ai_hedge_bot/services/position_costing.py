from __future__ import annotations

from typing import Any


def apply_fill_to_position_state(
    *,
    current_signed_qty: float,
    current_avg_entry_price: float | None,
    current_realized_pnl: float,
    fill_signed_qty: float,
    fill_price: float,
) -> tuple[dict[str, Any], float]:
    """
    Truth-based position costing.

    Rules
    -----
    - same direction add:
        avg_entry_price becomes weighted average
    - partial close:
        avg_entry_price is unchanged
    - full close:
        avg_entry_price becomes None
    - reverse:
        avg_entry_price becomes fill_price for the new side

    Returns
    -------
    updated_state, realized_delta
    """
    prev_qty = float(current_signed_qty or 0.0)
    prev_avg = (
        float(current_avg_entry_price)
        if current_avg_entry_price is not None
        else None
    )
    prev_realized = float(current_realized_pnl or 0.0)

    fill_qty = float(fill_signed_qty or 0.0)
    price = float(fill_price or 0.0)

    if abs(fill_qty) < 1e-12:
        updated = {
            "signed_qty": round(prev_qty, 8),
            "avg_entry_price": prev_avg,
            "realized_pnl": round(prev_realized, 8),
        }
        return updated, 0.0

    if abs(prev_qty) < 1e-12 or prev_avg is None:
        new_qty = prev_qty + fill_qty
        updated = {
            "signed_qty": round(new_qty, 8),
            "avg_entry_price": round(price, 8) if abs(new_qty) >= 1e-12 else None,
            "realized_pnl": round(prev_realized, 8),
        }
        return updated, 0.0

    same_direction = (prev_qty > 0 and fill_qty > 0) or (prev_qty < 0 and fill_qty < 0)

    if same_direction:
        new_qty = prev_qty + fill_qty
        weighted_avg = (
            (abs(prev_qty) * prev_avg) + (abs(fill_qty) * price)
        ) / max(abs(new_qty), 1e-12)
        updated = {
            "signed_qty": round(new_qty, 8),
            "avg_entry_price": round(weighted_avg, 8),
            "realized_pnl": round(prev_realized, 8),
        }
        return updated, 0.0

    close_qty = min(abs(prev_qty), abs(fill_qty))
    if prev_qty > 0:
        realized_delta = (price - prev_avg) * close_qty
    else:
        realized_delta = (prev_avg - price) * close_qty

    new_realized = prev_realized + realized_delta
    new_qty = prev_qty + fill_qty

    if abs(new_qty) < 1e-12:
        updated = {
            "signed_qty": 0.0,
            "avg_entry_price": None,
            "realized_pnl": round(new_realized, 8),
        }
        return updated, round(realized_delta, 8)

    if (prev_qty > 0 and new_qty > 0) or (prev_qty < 0 and new_qty < 0):
        updated = {
            "signed_qty": round(new_qty, 8),
            "avg_entry_price": round(prev_avg, 8),
            "realized_pnl": round(new_realized, 8),
        }
        return updated, round(realized_delta, 8)

    updated = {
        "signed_qty": round(new_qty, 8),
        "avg_entry_price": round(price, 8),
        "realized_pnl": round(new_realized, 8),
    }
    return updated, round(realized_delta, 8)