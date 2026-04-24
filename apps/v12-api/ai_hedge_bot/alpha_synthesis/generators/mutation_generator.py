from __future__ import annotations

from copy import deepcopy
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


class MutationAlphaGenerator:
    def __init__(self, seed: int = 202) -> None:
        self.rng = Random(seed)

    def _collect_nodes(self, node: AlphaNode, path: tuple[int, ...] = ()) -> list[tuple[tuple[int, ...], AlphaNode]]:
        rows = [(path, node)]
        for idx, child in enumerate(node.children):
            rows.extend(self._collect_nodes(child, path + (idx,)))
        return rows

    def _get_node(self, root: AlphaNode, path: tuple[int, ...]) -> AlphaNode:
        node = root
        for idx in path:
            node = node.children[idx]
        return node

    def mutate_one(self, expr: AlphaExpression) -> AlphaExpression:
        root = deepcopy(expr.root)
        nodes = self._collect_nodes(root)
        path, target = self.rng.choice(nodes)
        target = self._get_node(root, path)
        mutation_type = self.rng.choice(
            [
                "replace_feature",
                "replace_operator",
                "change_window",
                "wrap_with_unary_op",
                "insert_timeseries_op",
                "insert_cross_sectional_op",
            ]
        )

        if mutation_type == "replace_feature" and target.kind == "feature":
            target.value = self.rng.choice(FEATURE_CATALOG)
        elif mutation_type == "replace_operator":
            if target.kind == "unary":
                target.value = self.rng.choice(UNARY_OPERATORS)
            elif target.kind == "binary":
                target.value = self.rng.choice(BINARY_OPERATORS)
            elif target.kind == "timeseries":
                target.value = self.rng.choice(TIME_SERIES_OPERATORS)
            elif target.kind == "cross_sectional":
                target.value = self.rng.choice(CROSS_SECTIONAL_OPERATORS)
            elif target.kind == "feature":
                target.value = self.rng.choice(FEATURE_CATALOG)
        elif mutation_type == "change_window" and target.kind == "timeseries":
            target.window = self.rng.choice(WINDOW_CHOICES)
        elif mutation_type == "wrap_with_unary_op":
            replacement = AlphaNode(kind="unary", value=self.rng.choice(UNARY_OPERATORS), children=[deepcopy(target)])
            if path:
                parent = self._get_node(root, path[:-1])
                parent.children[path[-1]] = replacement
            else:
                root = replacement
        elif mutation_type == "insert_timeseries_op":
            replacement = AlphaNode(
                kind="timeseries",
                value=self.rng.choice(TIME_SERIES_OPERATORS),
                window=self.rng.choice(WINDOW_CHOICES),
                children=[deepcopy(target)],
            )
            if path:
                parent = self._get_node(root, path[:-1])
                parent.children[path[-1]] = replacement
            else:
                root = replacement
        elif mutation_type == "insert_cross_sectional_op":
            replacement = AlphaNode(kind="cross_sectional", value=self.rng.choice(CROSS_SECTIONAL_OPERATORS), children=[deepcopy(target)])
            if path:
                parent = self._get_node(root, path[:-1])
                parent.children[path[-1]] = replacement
            else:
                root = replacement
        else:
            target.value = self.rng.choice(FEATURE_CATALOG) if target.kind == "feature" else target.value

        return AlphaExpression.from_root(root)

    def generate_batch(self, parents: list[AlphaExpression], n: int) -> list[AlphaExpression]:
        if not parents:
            return []
        out: list[AlphaExpression] = []
        for _ in range(max(int(n), 0)):
            out.append(self.mutate_one(self.rng.choice(parents)))
        return out
