from __future__ import annotations

from ai_hedge_bot.alpha_ensemble.schemas import ValidatedAlpha


class EnsembleWeightAllocator:
    def allocate(
        self,
        ensemble_alpha_ids: list[str],
        alpha_by_id: dict[str, ValidatedAlpha],
        marginal_rows: list[dict],
        correlations: list[dict],
        max_weight_per_alpha: float = 0.25,
    ) -> list[dict]:
        marginal_lookup = {str(row.get("alpha_id") or ""): row for row in marginal_rows}
        corr_lookup: dict[tuple[str, str], float] = {}
        for row in correlations:
            key = tuple(sorted([str(row.get("alpha_id_a") or ""), str(row.get("alpha_id_b") or "")]))
            corr_lookup[key] = float(row.get("correlation", 0.0) or 0.0)

        raw_rows: list[dict] = []
        for alpha_id in ensemble_alpha_ids:
            alpha = alpha_by_id[alpha_id]
            marginal = marginal_lookup.get(alpha_id, {})
            peers = [peer_id for peer_id in ensemble_alpha_ids if peer_id != alpha_id]
            avg_abs_corr = (
                sum(corr_lookup.get(tuple(sorted([alpha_id, peer_id])), 0.0) for peer_id in peers) / len(peers)
                if peers
                else 0.0
            )
            quality = (
                (0.30 * alpha.aes_score)
                + (0.25 * alpha.validation_score)
                + (0.20 * alpha.robustness_score)
                + (0.15 * float(marginal.get("marginal_score", 0.0) or 0.0))
                + (0.10 * alpha.decay_score)
            )
            risk_adj = 1.0 / (0.15 + max(alpha.turnover, 0.01))
            corr_adj = 1.0 - min(max(avg_abs_corr, 0.0), 0.90)
            overfit_adj = 1.0 - min(max(alpha.overfit_risk, 0.0), 1.0)
            raw_weight = max(quality, 0.0) * (risk_adj ** 0.5) * corr_adj * overfit_adj * max(alpha.capacity_score, 0.05)
            raw_rows.append(
                {
                    "alpha_id": alpha_id,
                    "raw_weight": max(raw_weight, 0.0),
                    "capacity_cap": max(0.05, min(max_weight_per_alpha, alpha.capacity_score * 0.25)),
                    "avg_abs_corr": round(avg_abs_corr, 6),
                }
            )

        raw_total = sum(row["raw_weight"] for row in raw_rows)
        if raw_total <= 0:
            raw_total = float(len(raw_rows) or 1)
            for row in raw_rows:
                row["raw_weight"] = 1.0

        for row in raw_rows:
            row["normalized_weight"] = row["raw_weight"] / raw_total
            row["cap_adjusted_weight"] = min(row["normalized_weight"], row["capacity_cap"])

        capped_total = sum(row["cap_adjusted_weight"] for row in raw_rows)
        if capped_total <= 0:
            capped_total = float(len(raw_rows) or 1)
            for row in raw_rows:
                row["cap_adjusted_weight"] = 1.0

        items = []
        for row in raw_rows:
            final_weight = row["cap_adjusted_weight"] / capped_total
            items.append(
                {
                    "alpha_id": row["alpha_id"],
                    "raw_weight": round(row["raw_weight"], 6),
                    "normalized_weight": round(row["normalized_weight"], 6),
                    "cap_adjusted_weight": round(row["cap_adjusted_weight"], 6),
                    "final_weight": round(final_weight, 6),
                    "weight_reason": "robust_hybrid_weight",
                }
            )
        return items

