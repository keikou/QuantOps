from __future__ import annotations

from pathlib import Path
import json

from ai_hedge_bot.alpha.alpha_registry import ALPHA_REGISTRY


DEFAULT_WEIGHTS = {name: 1.0 for name in ALPHA_REGISTRY}


class AlphaWeightStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.save(DEFAULT_WEIGHTS)
        else:
            current = json.loads(self.path.read_text(encoding='utf-8'))
            merged = {**DEFAULT_WEIGHTS, **current}
            if merged != current:
                self.save(merged)

    def load(self) -> dict[str, float]:
        current = json.loads(self.path.read_text(encoding='utf-8'))
        merged = {**DEFAULT_WEIGHTS, **current}
        if merged != current:
            self.save(merged)
        return merged

    def save(self, weights: dict[str, float]) -> None:
        self.path.write_text(json.dumps(weights, ensure_ascii=False, indent=2), encoding='utf-8')

    def update_from_scores(self, alpha_scores: dict[str, float]) -> dict[str, float]:
        cur = self.load()
        new = {}
        for name, old in cur.items():
            score = alpha_scores.get(name, 0.0)
            bounded = max(-1.0, min(1.0, score))
            new[name] = round(max(0.2, min(2.5, old * 0.8 + (1.0 + bounded) * 0.2)), 6)
        self.save(new)
        return new
