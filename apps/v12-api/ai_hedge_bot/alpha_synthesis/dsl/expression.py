from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any

from ai_hedge_bot.alpha_synthesis.dsl.nodes import AlphaNode


def _formula(node: AlphaNode) -> str:
    if node.kind == "feature":
        return str(node.value)
    if node.kind == "constant":
        return str(node.value)
    if node.kind == "unary":
        return f"{node.value}({_formula(node.children[0])})"
    if node.kind == "binary":
        return f"{node.value}({_formula(node.children[0])}, {_formula(node.children[1])})"
    if node.kind == "timeseries":
        return f"{node.value}({_formula(node.children[0])}, {int(node.window or 0)})"
    if node.kind == "cross_sectional":
        return f"{node.value}({_formula(node.children[0])})"
    return "unknown()"


def _walk(node: AlphaNode) -> tuple[int, set[str], set[str]]:
    depth = 1
    features: set[str] = set()
    operators: set[str] = set()
    if node.kind == "feature":
        features.add(str(node.value))
    elif node.kind not in {"constant", ""}:
        operators.add(str(node.value))
    for child in node.children:
        child_depth, child_features, child_operators = _walk(child)
        depth = max(depth, 1 + child_depth)
        features |= child_features
        operators |= child_operators
    return depth, features, operators


def _node_count(node: AlphaNode) -> int:
    return 1 + sum(_node_count(child) for child in node.children)


def to_formula(expr: "AlphaExpression | AlphaNode") -> str:
    node = expr.root if isinstance(expr, AlphaExpression) else expr
    return _formula(node)


def to_json(expr: "AlphaExpression | AlphaNode") -> dict[str, Any]:
    node = expr.root if isinstance(expr, AlphaExpression) else expr
    return node.to_dict()


def from_json(payload: dict[str, Any]) -> "AlphaExpression":
    node = AlphaNode.from_dict(payload)
    return AlphaExpression.from_root(node)


def expression_hash(expr: "AlphaExpression | AlphaNode") -> str:
    payload = json.dumps(to_json(expr), ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


@dataclass
class AlphaExpression:
    root: AlphaNode
    formula: str
    expression_hash: str
    depth: int
    node_count: int
    feature_set: list[str]
    operator_set: list[str]

    @classmethod
    def from_root(cls, root: AlphaNode) -> "AlphaExpression":
        formula = _formula(root)
        depth, features, operators = _walk(root)
        node_count = _node_count(root)
        expr = cls(
            root=root,
            formula=formula,
            expression_hash="",
            depth=depth,
            node_count=node_count,
            feature_set=sorted(features),
            operator_set=sorted(operators),
        )
        expr.expression_hash = expression_hash(expr)
        return expr

