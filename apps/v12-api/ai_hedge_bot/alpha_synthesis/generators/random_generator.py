from __future__ import annotations

from random import Random

from ai_hedge_bot.alpha_synthesis.dsl.expression import AlphaExpression
from ai_hedge_bot.alpha_synthesis.dsl.nodes import AlphaNode
from ai_hedge_bot.alpha_synthesis.dsl.operators import (
    BINARY_OPERATORS,
    CROSS_SECTIONAL_OPERATORS,
    FEATURE_CATALOG,
    TIME_SERIES_OPERATORS,
    UNARY_OPERATORS,
    WINDOW_CHOICES,
)


class RandomAlphaGenerator:
    def __init__(self, seed: int = 101) -> None:
        self.rng = Random(seed)

    def _feature(self) -> AlphaNode:
        return AlphaNode(kind="feature", value=self.rng.choice(FEATURE_CATALOG))

    def _constant(self) -> AlphaNode:
        return AlphaNode(kind="constant", value=round(self.rng.uniform(-2.0, 2.0), 3))

    def _node(self, depth: int, max_depth: int) -> AlphaNode:
        if depth >= max_depth:
            return self._feature()
        choice = self.rng.choice(["feature", "unary", "binary", "timeseries", "cross"])
        if choice == "feature":
            return self._feature()
        if choice == "unary":
            return AlphaNode(kind="unary", value=self.rng.choice(UNARY_OPERATORS), children=[self._node(depth + 1, max_depth)])
        if choice == "binary":
            left = self._node(depth + 1, max_depth)
            right = self._feature() if self.rng.random() < 0.7 else self._constant()
            return AlphaNode(kind="binary", value=self.rng.choice(BINARY_OPERATORS), children=[left, right])
        if choice == "timeseries":
            return AlphaNode(
                kind="timeseries",
                value=self.rng.choice(TIME_SERIES_OPERATORS),
                window=self.rng.choice(WINDOW_CHOICES),
                children=[self._node(depth + 1, max_depth)],
            )
        return AlphaNode(kind="cross_sectional", value=self.rng.choice(CROSS_SECTIONAL_OPERATORS), children=[self._node(depth + 1, max_depth)])

    def generate_one(self, config: dict | None = None) -> AlphaExpression:
        config = config or {}
        max_depth = int(config.get("max_depth", 4) or 4)
        return AlphaExpression.from_root(self._node(0, max_depth))

    def generate_batch(self, n: int, config: dict | None = None) -> list[AlphaExpression]:
        return [self.generate_one(config=config) for _ in range(max(int(n), 0))]

