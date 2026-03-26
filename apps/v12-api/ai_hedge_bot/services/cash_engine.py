from __future__ import annotations


def compute_fill_cash_delta(
    *,
    signed_qty: float,
    fill_price: float,
    fee_bps: float = 0.0,
) -> tuple[float, float]:
    """
    Returns (delta_cash, fee).

    buy  => signed_qty > 0  => cash decreases
    sell => signed_qty < 0  => cash increases

    delta_cash = -(signed_qty * fill_price) - fee
    """
    qty = float(signed_qty or 0.0)
    price = float(fill_price or 0.0)
    fee_rate_bps = float(fee_bps or 0.0)

    fee = abs(qty) * price * fee_rate_bps / 10000.0
    delta_cash = -(qty * price) - fee
    return round(delta_cash, 8), round(fee, 8)