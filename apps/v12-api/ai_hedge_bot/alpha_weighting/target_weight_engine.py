from __future__ import annotations

from collections import defaultdict

from ai_hedge_bot.alpha_weighting.schemas import WeightingInput


class TargetWeightEngine:
    def compute(self, items: list[WeightingInput], states: dict[str, dict]) -> dict[str, float]:
        raw_by_ensemble: dict[str, list[tuple[str, float]]] = defaultdict(list)
        for item in items:
            state = states[item.alpha_id]
            multiplier = 0.45 + 1.10 * float(state["live_evidence_score"])
            if item.scaling_recommendation == "do_not_scale":
                multiplier *= 0.25
            elif item.scaling_recommendation == "scale_limited":
                multiplier *= 0.80
            raw_by_ensemble[item.ensemble_id].append((item.alpha_id, max(item.current_weight * multiplier, 0.0)))

        targets: dict[str, float] = {}
        for rows in raw_by_ensemble.values():
            total = sum(weight for _, weight in rows) or 1.0
            for alpha_id, weight in rows:
                targets[alpha_id] = round(weight / total, 6)
        return targets

