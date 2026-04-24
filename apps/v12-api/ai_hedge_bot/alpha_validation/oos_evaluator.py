from __future__ import annotations


class OOSEvaluator:
    def evaluate(self, window_metrics: dict) -> dict:
        train_score = float(window_metrics.get("train_score", 0.0) or 0.0)
        test_score = float(window_metrics.get("test_score", 0.0) or 0.0)
        test_sharpe = float(window_metrics.get("test_sharpe", 0.0) or 0.0)
        score_gap = round(train_score - test_score, 6)
        degradation_ratio = round(test_score / (train_score + 1e-9), 6)
        fail_reason = ""
        passed = True
        if test_score < 0.45:
            fail_reason = "low_oos_score"
            passed = False
        elif degradation_ratio < 0.50:
            fail_reason = "degraded_oos_score"
            passed = False
        elif test_sharpe < 0.25:
            fail_reason = "low_oos_sharpe"
            passed = False
        return {
            "score_gap": score_gap,
            "degradation_ratio": degradation_ratio,
            "passed": passed,
            "fail_reason": fail_reason,
        }

