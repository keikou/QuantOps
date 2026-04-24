from __future__ import annotations

import hashlib

from ai_hedge_bot.alpha_synthesis.dsl.expression import AlphaExpression


class ExpressionEvaluator:
    def evaluate(self, expr: AlphaExpression) -> dict[str, float | bool]:
        digest = hashlib.sha256(expr.formula.encode("utf-8")).hexdigest()
        base = int(digest[:8], 16)
        variance_score = round(((base % 7000) / 7000.0), 6)
        turnover_proxy = round((((base // 7) % 5000) / 10000.0), 6)
        instability_score = round((((base // 13) % 3000) / 10000.0), 6)
        return {
            "output_exists": True,
            "variance_score": variance_score,
            "turnover_proxy": turnover_proxy,
            "instability_score": instability_score,
            "all_null": False,
            "constant_like": variance_score < 0.08,
        }

