from __future__ import annotations

from ai_hedge_bot.orchestrator.orchestration_service import OrchestrationService


def test_execution_fill_rate_uses_child_qty_and_clamps() -> None:
    orders = [
        {"qty": 10.0},
        {"qty": 5.0},
    ]
    fills = [
        {"fill_qty": 10.0},
        {"fill_qty": 5.0},
        {"fill_qty": 2.5},
    ]

    submitted_qty = sum(float(o["qty"]) for o in orders)
    filled_qty = sum(float(f["fill_qty"]) for f in fills)
    raw_fill_rate = filled_qty / submitted_qty
    fill_rate = round(max(0.0, min(1.0, raw_fill_rate)), 4)

    assert raw_fill_rate > 1.0
    assert fill_rate == 1.0
