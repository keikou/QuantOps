from __future__ import annotations

from ai_hedge_bot.alpha_synthesis.dsl.expression import AlphaExpression


def _jaccard_distance(left: set[str], right: set[str]) -> float:
    union = left | right
    if not union:
        return 0.0
    return round(1.0 - (len(left & right) / len(union)), 6)


def score_structural_novelty(expr: AlphaExpression, library_rows: list[dict]) -> dict:
    if not library_rows:
        return {
            "nearest_expression_id": None,
            "exact_duplicate": False,
            "operator_jaccard_distance": 1.0,
            "feature_jaccard_distance": 1.0,
            "token_distance": 1.0,
            "novelty_score": 1.0,
            "novelty_verdict": "novel",
        }

    best = None
    best_score = -1.0
    expr_tokens = set(expr.formula.replace("(", " ").replace(")", " ").replace(",", " ").split())
    expr_features = set(expr.feature_set)
    expr_operators = set(expr.operator_set)

    for row in library_rows:
        row_tokens = set(str(row.get("formula") or "").replace("(", " ").replace(")", " ").replace(",", " ").split())
        row_features = set(list(row.get("feature_set") or []))
        row_operators = set(list(row.get("operator_set") or []))
        feature_dist = _jaccard_distance(expr_features, row_features)
        operator_dist = _jaccard_distance(expr_operators, row_operators)
        token_dist = _jaccard_distance(expr_tokens, row_tokens)
        score = round((feature_dist + operator_dist + token_dist) / 3.0, 6)
        if score > best_score:
            best_score = score
            best = {
                "nearest_expression_id": row.get("expression_id"),
                "exact_duplicate": str(row.get("expression_hash") or "") == expr.expression_hash,
                "operator_jaccard_distance": operator_dist,
                "feature_jaccard_distance": feature_dist,
                "token_distance": token_dist,
                "novelty_score": score,
            }

    verdict = "duplicate" if best and best["exact_duplicate"] else "near_duplicate" if best_score < 0.35 else "novel"
    return {**(best or {}), "novelty_verdict": verdict}

