from __future__ import annotations

from ai_hedge_bot.operational_risk.schemas import RISK_LEVEL_ORDER


class RiskStateEngine:
    DOMAINS = ["data", "execution", "portfolio", "alpha_system", "infra"]

    def compute(self, incidents: list[dict]) -> dict:
        domain_levels = {domain: "L0_NORMAL" for domain in self.DOMAINS}
        for incident in incidents:
            domain = str(incident["domain"])
            current = domain_levels.get(domain, "L0_NORMAL")
            candidate = str(incident["risk_level"])
            if RISK_LEVEL_ORDER[candidate] > RISK_LEVEL_ORDER[current]:
                domain_levels[domain] = candidate
        global_level = max(domain_levels.values(), key=lambda level: RISK_LEVEL_ORDER[level])
        return {
            "global_risk_level": global_level,
            "data_risk_level": domain_levels["data"],
            "execution_risk_level": domain_levels["execution"],
            "portfolio_risk_level": domain_levels["portfolio"],
            "alpha_system_risk_level": domain_levels["alpha_system"],
            "infra_risk_level": domain_levels["infra"],
            "recommended_action": self._action(global_level),
            "action_required": global_level != "L0_NORMAL",
            "reason": "max_domain_risk_level",
        }

    def _action(self, level: str) -> str:
        return {
            "L0_NORMAL": "no_action",
            "L1_WATCH": "notify_and_monitor",
            "L2_REDUCE": "reduce_exposure",
            "L3_FREEZE": "freeze_new_exposure",
            "L4_PARTIAL_HALT": "halt_affected_scope",
            "L5_GLOBAL_HALT": "halt_all_new_risk",
        }.get(level, "notify_and_monitor")

