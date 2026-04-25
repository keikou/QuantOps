from __future__ import annotations

from ai_hedge_bot.authorization.schemas import SAFETY_WEAKENING_ACTIONS


class HardSafetyAuthorization:
    def denied(self, hard_safety_flag: bool, action: str) -> str:
        if hard_safety_flag and action in SAFETY_WEAKENING_ACTIONS:
            return "hard_safety_bypass_denied"
        return ""

