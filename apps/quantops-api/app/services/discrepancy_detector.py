from __future__ import annotations

from typing import Any


def compare_equity_fields(
    v12_snapshot: dict[str, Any],
    quantops_payload: dict[str, Any],
    *,
    tolerance: float = 1e-6,
) -> list[dict[str, Any]]:
    """
    Compare truth values from V12 against QuantOps-computed/rendered values.
    """
    fields = [
        "cash_balance",
        "market_value",
        "total_equity",
        "realized_pnl",
        "unrealized_pnl",
        "gross_exposure",
        "net_exposure",
    ]

    mismatches: list[dict[str, Any]] = []
    for field_name in fields:
        expected = _to_float(v12_snapshot.get(field_name))
        actual = _to_float(quantops_payload.get(field_name))
        delta = actual - expected
        if abs(delta) > tolerance:
            mismatches.append(
                {
                    "category": "equity_truth_mismatch",
                    "field_name": field_name,
                    "expected_value": expected,
                    "actual_value": actual,
                    "delta_value": round(delta, 8),
                    "severity": _severity(field_name, delta),
                }
            )
    return mismatches


def _to_float(value: Any) -> float:
    try:
        return float(value or 0.0)
    except Exception:
        return 0.0


def _severity(field_name: str, delta: float) -> str:
    mag = abs(delta)
    if field_name == "total_equity":
        if mag >= 100.0:
            return "high"
        if mag >= 1.0:
            return "medium"
        return "low"
    if mag >= 10.0:
        return "medium"
    return "low"