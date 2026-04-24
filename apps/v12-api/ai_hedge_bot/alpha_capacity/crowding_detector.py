from __future__ import annotations

from ai_hedge_bot.alpha_capacity.schemas import CapacityInput


class CrowdingDetector:
    def score(self, item: CapacityInput) -> dict:
        correlation_cluster_score = min(1.0, item.max_factor_concentration * 0.72)
        factor_concentration = min(1.0, item.factor_concentration_score)
        signal_overlap = min(1.0, 0.25 + item.weight * 0.9)
        volume_anomaly = min(1.0, 0.18 + item.turnover * 0.7)
        crowding_score = (
            0.40 * correlation_cluster_score
            + 0.30 * factor_concentration
            + 0.20 * signal_overlap
            + 0.10 * volume_anomaly
        )
        return {
            "correlation_cluster_score": round(correlation_cluster_score, 6),
            "factor_concentration": round(factor_concentration, 6),
            "signal_overlap": round(signal_overlap, 6),
            "volume_anomaly": round(volume_anomaly, 6),
            "crowding_score": round(min(1.0, crowding_score), 6),
        }

