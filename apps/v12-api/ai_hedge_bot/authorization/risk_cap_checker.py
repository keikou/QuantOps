from __future__ import annotations

from ai_hedge_bot.authorization.schemas import RISK_RANK


class RiskCapChecker:
    def allowed(self, role_cap: str, requested_risk: str) -> bool:
        return RISK_RANK.get(requested_risk, 4) <= RISK_RANK.get(role_cap, 0)

    def approval_action_for_risk(self, risk_level: str) -> str:
        rank = RISK_RANK.get(risk_level, 4)
        if rank <= 1:
            return "approval.approve.low"
        if rank == 2:
            return "approval.approve.medium"
        if rank == 3:
            return "approval.approve.high"
        return "approval.approve.critical"

