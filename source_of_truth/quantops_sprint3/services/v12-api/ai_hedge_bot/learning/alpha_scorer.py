from __future__ import annotations


def score_alpha(hit_rate: float, avg_1h_return: float, avg_4h_return: float, avg_mae: float) -> float:
    return max(-1.0, min(1.0, 0.4 * hit_rate + 10.0 * avg_1h_return + 10.0 * avg_4h_return + 2.0 * avg_mae))
