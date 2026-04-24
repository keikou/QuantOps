from __future__ import annotations

from ai_hedge_bot.alpha_attribution.schemas import SelectedAlpha


class HiddenDriverDetector:
    def detect(self, alphas: list[SelectedAlpha]) -> list[dict]:
        items: list[dict] = []
        for idx, left in enumerate(alphas):
            for right in alphas[idx + 1 :]:
                residual_corr = 0.22 + (0.24 if left.alpha_family == right.alpha_family else 0.0) + (0.10 if left.regime == right.regime else 0.0)
                common_driver_score = (0.60 * residual_corr) + (0.25 * (1.0 if left.alpha_family == right.alpha_family else 0.2)) + (0.15 * (1.0 if left.regime == right.regime else 0.3))
                suspected_driver = "shared_family_driver" if left.alpha_family == right.alpha_family else ("shared_regime_driver" if left.regime == right.regime else "unknown_common_driver")
                items.append(
                    {
                        "alpha_id_a": left.alpha_id,
                        "alpha_id_b": right.alpha_id,
                        "common_driver_score": round(common_driver_score, 6),
                        "residual_correlation": round(residual_corr, 6),
                        "suspected_driver": suspected_driver,
                        "flag": common_driver_score >= 0.80,
                    }
                )
        return items

