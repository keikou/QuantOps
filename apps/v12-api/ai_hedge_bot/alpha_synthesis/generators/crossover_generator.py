from __future__ import annotations

from copy import deepcopy
from random import Random

from ai_hedge_bot.alpha_synthesis.dsl.expression import AlphaExpression
from ai_hedge_bot.alpha_synthesis.dsl.nodes import AlphaNode


class CrossoverAlphaGenerator:
    def __init__(self, seed: int = 303) -> None:
        self.rng = Random(seed)

    def _collect_paths(self, node: AlphaNode, path: tuple[int, ...] = ()) -> list[tuple[int, ...]]:
        rows = [path]
        for idx, child in enumerate(node.children):
            rows.extend(self._collect_paths(child, path + (idx,)))
        return rows

    def _get_node(self, root: AlphaNode, path: tuple[int, ...]) -> AlphaNode:
        node = root
        for idx in path:
            node = node.children[idx]
        return node

    def crossover_one(self, left: AlphaExpression, right: AlphaExpression) -> AlphaExpression:
        root = deepcopy(left.root)
        left_paths = self._collect_paths(root)
        right_paths = self._collect_paths(right.root)
        left_path = self.rng.choice(left_paths)
        right_path = self.rng.choice(right_paths)
        replacement = deepcopy(self._get_node(right.root, right_path))
        if left_path:
            parent = self._get_node(root, left_path[:-1])
            parent.children[left_path[-1]] = replacement
        else:
            root = replacement
        return AlphaExpression.from_root(root)

    def generate_batch(self, parents: list[AlphaExpression], n: int) -> list[AlphaExpression]:
        if len(parents) < 2:
            return []
        out: list[AlphaExpression] = []
        for _ in range(max(int(n), 0)):
            left, right = self.rng.sample(parents, 2)
            out.append(self.crossover_one(left, right))
        return out
