from __future__ import annotations

from ai_hedge_bot.alpha_synthesis.dsl.expression import AlphaExpression
from ai_hedge_bot.alpha_synthesis.generators.crossover_generator import CrossoverAlphaGenerator
from ai_hedge_bot.alpha_synthesis.generators.hypothesis_generator import HypothesisAlphaGenerator
from ai_hedge_bot.alpha_synthesis.generators.mutation_generator import MutationAlphaGenerator
from ai_hedge_bot.alpha_synthesis.generators.random_generator import RandomAlphaGenerator


class AlphaGenerationRouter:
    def __init__(self) -> None:
        self.random = RandomAlphaGenerator(seed=101)
        self.mutation = MutationAlphaGenerator(seed=202)
        self.crossover = CrossoverAlphaGenerator(seed=303)
        self.hypothesis = HypothesisAlphaGenerator(seed=404)

    def generate(self, mode: str, *, parents: list[AlphaExpression], n: int, config: dict | None = None) -> list[AlphaExpression]:
        normalized = str(mode or "random")
        config = config or {}
        if normalized == "mutation":
            return self.mutation.generate_batch(parents, n=n)
        if normalized == "crossover":
            return self.crossover.generate_batch(parents, n=n)
        if normalized == "hypothesis":
            return self.hypothesis.generate_batch(list(config.get("briefs") or []), n=n)
        return self.random.generate_batch(n=n, config=config)
