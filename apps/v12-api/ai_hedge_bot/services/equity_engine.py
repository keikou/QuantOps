from __future__ import annotations

from typing import Any


def compute_equity_snapshot_row(
    *,
    cash_balance: float,
    positions: list[dict[str, Any]],
    previous_peak_equity: float,
    reporting_currency: str = "USD",
    venue_id: str | None = None,
    account_id: str | None = None,
    as_of: str | None = None,
) -> dict[str, Any]:
    market_value = round(
        sum(float(p.get("market_value", 0.0) or 0.0) for p in positions),
        8,
    )
    unrealized_pnl = round(
        sum(float(p.get("unrealized_pnl", 0.0) or 0.0) for p in positions),
        8,
    )
    realized_pnl = round(
        sum(float(p.get("realized_pnl", 0.0) or 0.0) for p in positions),
        8,
    )

    long_value = round(
        sum(
            max(0.0, float(p.get("market_value", 0.0) or 0.0))
            for p in positions
        ),
        8,
    )
    short_value = round(
        sum(
            abs(min(0.0, float(p.get("market_value", 0.0) or 0.0)))
            for p in positions
        ),
        8,
    )

    total_equity = round(float(cash_balance or 0.0) + market_value, 8)
    gross_exposure = round(long_value + short_value, 8)
    net_exposure = round(market_value, 8)

    previous_peak = float(previous_peak_equity or 0.0)
    peak_equity = round(max(previous_peak, total_equity), 8)
    drawdown = (
        round((peak_equity - total_equity) / peak_equity, 8)
        if peak_equity > 0
        else 0.0
    )

    return {
        "snapshot_time": as_of,
        "venue_id": venue_id,
        "account_id": account_id,
        "reporting_currency": reporting_currency,
        "cash_balance": round(float(cash_balance or 0.0), 8),
        "gross_exposure": gross_exposure,
        "net_exposure": net_exposure,
        "long_exposure": long_value,
        "short_exposure": short_value,
        "market_value": market_value,
        "unrealized_pnl": unrealized_pnl,
        "realized_pnl": realized_pnl,
        "total_equity": total_equity,
        "drawdown": drawdown,
        "peak_equity": peak_equity,
    }