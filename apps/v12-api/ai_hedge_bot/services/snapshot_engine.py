from __future__ import annotations

from typing import Any


def build_position_snapshot_rows(
    *,
    states: dict[tuple[str, ...], dict[str, Any]],
    price_by_symbol: dict[str, dict[str, Any]],
    as_of: str,
    snapshot_version: str,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    for _, state in states.items():
        symbol = str(state["symbol"])
        signed_qty = float(state.get("signed_qty", 0.0) or 0.0)

        if abs(signed_qty) < 1e-12:
            continue

        avg_entry_price = (
            float(state["avg_entry_price"])
            if state.get("avg_entry_price") is not None
            else None
        )
        price_meta = dict(price_by_symbol.get(symbol) or {})

        mark_price = float(
            price_meta.get("mark_price")
            or price_meta.get("mid")
            or price_meta.get("last")
            or avg_entry_price
            or 0.0
        )

        market_value = round(signed_qty * mark_price, 8)
        unrealized_pnl = 0.0
        if avg_entry_price is not None:
            unrealized_pnl = round((mark_price - avg_entry_price) * signed_qty, 8)

        rows.append(
            {
                "snapshot_version": snapshot_version,
                "symbol": symbol,
                "strategy_id": state.get("strategy_id") or "paper_runtime",
                "alpha_family": state.get("alpha_family") or "runtime",
                "venue_id": state.get("venue_id"),
                "account_id": state.get("account_id"),
                "signed_qty": round(signed_qty, 8),
                "abs_qty": round(abs(signed_qty), 8),
                "side": "long" if signed_qty > 0 else "short",
                "avg_entry_price": round(avg_entry_price, 8)
                if avg_entry_price is not None
                else None,
                "mark_price": round(mark_price, 8),
                "market_value": market_value,
                "unrealized_pnl": unrealized_pnl,
                "realized_pnl": round(float(state.get("realized_pnl", 0.0) or 0.0), 8),
                "exposure_notional": round(abs(market_value), 8),
                "price_source": price_meta.get("source", "missing_mark_price"),
                "quote_time": price_meta.get("price_time", as_of),
                "quote_age_sec": float(price_meta.get("quote_age_sec", 0.0) or 0.0),
                "stale": bool(price_meta.get("stale", False)),
                "updated_at": as_of,
                "reporting_currency": state.get("reporting_currency", "USD"),
            }
        )

    rows.sort(key=lambda item: (item["exposure_notional"], item["symbol"]), reverse=True)
    return rows