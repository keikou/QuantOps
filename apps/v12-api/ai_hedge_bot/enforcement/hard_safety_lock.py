from __future__ import annotations

from ai_hedge_bot.enforcement.schemas import RISK_INCREASING_ACTIONS, RISK_INCREASING_ORDER_MODES, SAFETY_STRENGTHENING_ACTIONS


class HardSafetyLock:
    def check(self, request: dict, context: dict) -> dict | None:
        if not context.get("hard_safety_flag"):
            return None
        action = str(request.get("action_type") or "")
        order_mode = str(request.get("order_mode") or action)
        if action in SAFETY_STRENGTHENING_ACTIONS or order_mode in {"reduce", "close", "cancel"}:
            return None
        if action in RISK_INCREASING_ACTIONS or order_mode in RISK_INCREASING_ORDER_MODES:
            return {
                "decision": "BLOCK",
                "reason": "hard_safety_lock_blocks_risk_increasing_action",
                "violations": [{"type": "hard_safety_violation", "severity": "critical", "reason": "hard safety active"}],
            }
        return None

