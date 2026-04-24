from __future__ import annotations

from ai_hedge_bot.alpha_synthesis.dsl.expression import AlphaExpression
from ai_hedge_bot.alpha_synthesis.dsl.operators import (
    BINARY_OPERATORS,
    CROSS_SECTIONAL_OPERATORS,
    FEATURE_CATALOG,
    TIME_SERIES_OPERATORS,
    UNARY_OPERATORS,
    WINDOW_CHOICES,
)

MAX_DEPTH = 6
MAX_NODE_COUNT = 32


def validate_expression(expr: AlphaExpression) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    if expr.depth > MAX_DEPTH:
        reasons.append("max_depth_exceeded")
    if expr.node_count > MAX_NODE_COUNT:
        reasons.append("max_node_count_exceeded")
    if not expr.feature_set:
        reasons.append("constant_only_expression")
    if len(set(expr.feature_set)) < 1:
        reasons.append("feature_diversity_too_low")

    def _validate_node(node) -> None:
        if node.kind == "feature" and str(node.value) not in FEATURE_CATALOG:
            reasons.append(f"unsupported_feature:{node.value}")
        elif node.kind == "unary" and str(node.value) not in UNARY_OPERATORS:
            reasons.append(f"unsupported_unary:{node.value}")
        elif node.kind == "binary":
            if str(node.value) not in BINARY_OPERATORS:
                reasons.append(f"unsupported_binary:{node.value}")
            if str(node.value) == "div_safe" and len(node.children) != 2:
                reasons.append("div_safe_arity_invalid")
        elif node.kind == "timeseries":
            if str(node.value) not in TIME_SERIES_OPERATORS:
                reasons.append(f"unsupported_timeseries:{node.value}")
            if int(node.window or 0) not in WINDOW_CHOICES:
                reasons.append("window_out_of_bounds")
        elif node.kind == "cross_sectional" and str(node.value) not in CROSS_SECTIONAL_OPERATORS:
            reasons.append(f"unsupported_cross_sectional:{node.value}")
        for child in node.children:
            _validate_node(child)

    _validate_node(expr.root)
    return not reasons, sorted(set(reasons))

