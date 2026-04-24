from __future__ import annotations

from ai_hedge_bot.alpha_ensemble.schemas import EnsembleCandidate, ValidatedAlpha


class EnsembleCandidateGenerator:
    def generate(self, alphas: list[ValidatedAlpha], limit: int = 8, max_alpha_count: int = 5, max_per_family: int = 2) -> list[EnsembleCandidate]:
        ranked = sorted(alphas, key=lambda item: (-item.validation_score, -item.aes_score, item.alpha_id))
        if not ranked:
            return []

        candidates: list[EnsembleCandidate] = []
        seen: set[tuple[str, ...]] = set()

        def add_candidate(alpha_subset: list[ValidatedAlpha], source: str) -> None:
            family_counts: dict[str, int] = {}
            final_items: list[ValidatedAlpha] = []
            for alpha in alpha_subset:
                count = family_counts.get(alpha.alpha_family, 0)
                if count >= max_per_family:
                    continue
                family_counts[alpha.alpha_family] = count + 1
                final_items.append(alpha)
                if len(final_items) >= max_alpha_count:
                    break
            key = tuple(sorted(item.alpha_id for item in final_items))
            if len(key) < 2 or key in seen:
                return
            seen.add(key)
            candidates.append(
                EnsembleCandidate(
                    ensemble_id=f"ensemble.{len(candidates) + 1}",
                    alpha_ids=list(key),
                    source=source,
                )
            )

        add_candidate(ranked[:max_alpha_count], "top_validation_seed")

        family_seen: set[str] = set()
        diversified: list[ValidatedAlpha] = []
        for alpha in ranked:
            if alpha.alpha_family in family_seen and len(diversified) >= 2:
                continue
            family_seen.add(alpha.alpha_family)
            diversified.append(alpha)
            if len(diversified) >= max_alpha_count:
                break
        add_candidate(diversified, "family_diversified_seed")

        for idx in range(min(len(ranked), max(limit * 2, 6))):
            rotated = ranked[idx:] + ranked[:idx]
            add_candidate(rotated[:max_alpha_count], f"rotated_seed_{idx + 1}")
            if len(candidates) >= limit:
                break
        return candidates[:limit]

