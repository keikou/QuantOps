from __future__ import annotations

from statistics import mean, median


class StabilityAnalyzer:
    def summarize(self, items: list[dict]) -> dict:
        if not items:
            return {
                "total_windows": 0,
                "passed_windows": 0,
                "pass_rate": 0.0,
                "mean_oos_score": 0.0,
                "median_oos_score": 0.0,
                "mean_degradation_ratio": 0.0,
                "worst_window_score": 0.0,
                "stability_score": 0.0,
            }
        test_scores = [float(item.get("test_score", 0.0) or 0.0) for item in items]
        degradation = [float(item.get("degradation_ratio", 0.0) or 0.0) for item in items]
        passed_windows = sum(1 for item in items if bool(item.get("passed")))
        avg = mean(test_scores)
        variance = sum((value - avg) ** 2 for value in test_scores) / len(test_scores)
        normalized_std = min(1.0, variance ** 0.5)
        stability_score = round(max(0.0, 1 - normalized_std), 6)
        return {
            "total_windows": len(items),
            "passed_windows": passed_windows,
            "pass_rate": round(passed_windows / len(items), 6),
            "mean_oos_score": round(avg, 6),
            "median_oos_score": round(median(test_scores), 6),
            "mean_degradation_ratio": round(mean(degradation), 6),
            "worst_window_score": round(min(test_scores), 6),
            "stability_score": stability_score,
        }

