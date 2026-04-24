from __future__ import annotations

from collections import defaultdict

from ai_hedge_bot.alpha_weighting.schemas import WeightingInput


class ConstraintEngine:
    def __init__(self, max_weight: float = 0.45, max_delta: float = 0.05) -> None:
        self.max_weight = max_weight
        self.max_delta = max_delta

    def apply(self, items: list[WeightingInput], smoothed: dict[str, float]) -> tuple[dict[str, float], dict[str, dict]]:
        constrained_raw: dict[str, float] = {}
        constraints: dict[str, dict] = {}
        for item in items:
            proposed = float(smoothed[item.alpha_id])
            lower = max(0.0, item.current_weight - self.max_delta)
            upper = min(self.max_weight, item.current_weight + self.max_delta)
            constrained = min(max(proposed, lower), upper)
            if item.scaling_recommendation == "do_not_scale":
                constrained = min(constrained, item.current_weight)
            action = "accepted"
            if abs(constrained - proposed) > 0.000001:
                action = "turnover_or_capacity_capped"
            constrained_raw[item.alpha_id] = constrained
            constraints[item.alpha_id] = {
                "max_weight": self.max_weight,
                "max_delta": self.max_delta,
                "lower_bound": round(lower, 6),
                "upper_bound": round(upper, 6),
                "constraint_action": action,
            }

        by_ensemble: dict[str, list[str]] = defaultdict(list)
        lookup = {item.alpha_id: item for item in items}
        for alpha_id in constrained_raw:
            by_ensemble[lookup[alpha_id].ensemble_id].append(alpha_id)

        final: dict[str, float] = {}
        for alpha_ids in by_ensemble.values():
            total = sum(constrained_raw[alpha_id] for alpha_id in alpha_ids) or 1.0
            for alpha_id in alpha_ids:
                final[alpha_id] = round(constrained_raw[alpha_id] / total, 6)
        return final, constraints

