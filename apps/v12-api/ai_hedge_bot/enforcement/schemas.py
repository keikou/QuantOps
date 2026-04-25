from __future__ import annotations

RISK_ORDER = {
    "L0_NORMAL": 0,
    "L1_WATCH": 1,
    "L2_REDUCE": 2,
    "L3_FREEZE": 3,
    "L4_PARTIAL_HALT": 4,
    "L5_GLOBAL_HALT": 5,
}

RISK_INCREASING_ACTIONS = {
    "open_new",
    "increase",
    "increase_allocation",
    "promote_alpha",
    "resume_alpha",
    "policy_relaxation",
    "increase_weight",
}

RISK_REDUCING_ORDER_MODES = {"reduce", "close", "cancel"}
RISK_INCREASING_ORDER_MODES = {"open_new", "increase", "replace_increase_qty"}
SAFETY_STRENGTHENING_ACTIONS = {"reduce", "close", "cancel", "freeze_alpha", "retire_alpha", "policy_tightening", "global_halt", "partial_halt"}


def risk_at_least(current: str, threshold: str) -> bool:
    return RISK_ORDER.get(current, 5) >= RISK_ORDER.get(threshold, 5)

