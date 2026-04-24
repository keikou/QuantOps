from __future__ import annotations

from statistics import median


class RobustnessEngine:
    def evaluate(self, rows: list[dict]) -> dict:
        values = [float(row.get("cost_adjusted_return", 0.0) or 0.0) for row in rows]
        if not values:
            return {
                "mean_return": 0.0,
                "median_return": 0.0,
                "hit_rate": 0.0,
                "sharpe_like": 0.0,
                "sharpe_robust": 0.0,
                "sharpe_final": 0.0,
                "robustness_score": 0.0,
            }
        avg = sum(values) / len(values)
        med = median(values)
        variance = sum((value - avg) ** 2 for value in values) / len(values)
        sigma = (variance + 1e-9) ** 0.5
        mad = median(abs(value - med) for value in values) + 1e-9
        hit_rate = sum(1 for value in values if value > 0) / len(values)
        sharpe_like = (avg / sigma) * (252 ** 0.5)
        sharpe_robust = med / mad
        sharpe_final = (0.7 * sharpe_like) + (0.3 * sharpe_robust)
        robustness_score = max(0.0, min(((hit_rate + max(sharpe_final, 0.0)) / 2.0), 1.0))
        return {
            "mean_return": round(avg, 6),
            "median_return": round(med, 6),
            "hit_rate": round(hit_rate, 6),
            "sharpe_like": round(sharpe_like, 6),
            "sharpe_robust": round(sharpe_robust, 6),
            "sharpe_final": round(sharpe_final, 6),
            "robustness_score": round(robustness_score, 6),
        }

