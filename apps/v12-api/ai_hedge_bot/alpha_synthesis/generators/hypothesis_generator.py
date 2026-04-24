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


class HypothesisAlphaGenerator:
    def __init__(self, seed: int = 404) -> None:
        self.rng = Random(seed)

    def _pick_feature(self, preferred: list[str], fallback: list[str] | None = None) -> str:
        universe = list(preferred or []) + list(fallback or []) + list(FEATURE_CATALOG)
        return self.rng.choice([item for item in universe if item])

    def _pick_operator(self, preferred: list[str], fallback: list[str]) -> str:
        universe = list(preferred or []) + list(fallback)
        return self.rng.choice([item for item in universe if item])

    def _expression_from_brief(self, brief: dict) -> AlphaExpression:
        preferred_features = list(brief.get("preferred_features") or [])
        preferred_operators = list(brief.get("preferred_operators") or [])
        regime_bias = str(brief.get("regime_bias") or "observe")

        feature_a = AlphaNode(kind="feature", value=self._pick_feature(preferred_features))
        feature_b = AlphaNode(kind="feature", value=self._pick_feature(preferred_features, fallback=["returns", "volume", "volatility"]))

        binary = AlphaNode(
            kind="binary",
            value=self._pick_operator(preferred_operators, BINARY_OPERATORS),
            children=[feature_a, feature_b],
        )
        ts_node = AlphaNode(
            kind="timeseries",
            value=self._pick_operator(preferred_operators, TIME_SERIES_OPERATORS),
            window=self.rng.choice(WINDOW_CHOICES),
            children=[binary],
        )

        if regime_bias == "constrain":
            unary = AlphaNode(kind="unary", value="winsorize", children=[ts_node])
            root = AlphaNode(kind="cross_sectional", value="cs_zscore", children=[unary])
        elif regime_bias == "adapt":
            unary = AlphaNode(kind="unary", value=self._pick_operator(preferred_operators, UNARY_OPERATORS), children=[ts_node])
            root = AlphaNode(kind="cross_sectional", value="normalize", children=[unary])
        elif regime_bias == "expand":
            root = AlphaNode(
                kind="cross_sectional",
                value=self._pick_operator(preferred_operators, CROSS_SECTIONAL_OPERATORS),
                children=[ts_node],
            )
        else:
            root = AlphaNode(kind="cross_sectional", value="rank", children=[ts_node])

        return AlphaExpression.from_root(root)

    def generate_batch(self, briefs: list[dict], n: int) -> list[AlphaExpression]:
        if not briefs:
            return []
        out: list[AlphaExpression] = []
        normalized_n = max(int(n), 0)
        for idx in range(normalized_n):
            brief = briefs[idx % len(briefs)]
            out.append(self._expression_from_brief(brief))
        return out
