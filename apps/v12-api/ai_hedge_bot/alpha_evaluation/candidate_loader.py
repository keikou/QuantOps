from __future__ import annotations

from ai_hedge_bot.alpha_evaluation.schemas import AlphaEvaluationCandidate
from ai_hedge_bot.app.container import CONTAINER


class AlphaCandidateLoader:
    def __init__(self) -> None:
        self.store = CONTAINER.runtime_store

    def load_latest_candidates(self, limit: int = 50) -> list[AlphaEvaluationCandidate]:
        library_rows = self.store.fetchall_dict(
            """
            SELECT *
            FROM alpha_library
            ORDER BY created_at DESC, alpha_id ASC
            LIMIT ?
            """,
            [max(int(limit) * 3, 50)],
        )
        ranking_rows = self.store.fetchall_dict(
            """
            SELECT *
            FROM alpha_rankings
            ORDER BY created_at DESC, alpha_id ASC
            LIMIT ?
            """,
            [max(int(limit) * 3, 50)],
        )
        expression_rows = self.store.fetchall_dict(
            """
            SELECT *
            FROM alpha_expression_library
            WHERE status='accepted'
            ORDER BY created_at DESC, expression_id ASC
            LIMIT ?
            """,
            [max(int(limit) * 3, 50)],
        )

        ranking_by_alpha = {}
        for row in ranking_rows:
            alpha_id = str(row.get("alpha_id") or "")
            if alpha_id and alpha_id not in ranking_by_alpha:
                ranking_by_alpha[alpha_id] = row

        latest_expression = expression_rows[0] if expression_rows else {}
        feature_set = self.store.parse_json(latest_expression.get("feature_set_json"), []) or []
        operator_set = self.store.parse_json(latest_expression.get("operator_set_json"), []) or []

        out: list[AlphaEvaluationCandidate] = []
        seen: set[str] = set()
        for row in library_rows:
            alpha_id = str(row.get("alpha_id") or "")
            if not alpha_id or alpha_id in seen:
                continue
            seen.add(alpha_id)
            ranking = dict(ranking_by_alpha.get(alpha_id) or {})
            out.append(
                AlphaEvaluationCandidate(
                    alpha_id=alpha_id,
                    alpha_family=str(row.get("alpha_family") or "unknown"),
                    source="aae_asd_bridge",
                    rank_score=float(ranking.get("rank_score", 0.0) or 0.0),
                    expected_return=float(ranking.get("expected_return", 0.0) or 0.0),
                    execution_cost_adjusted_score=float(ranking.get("execution_cost_adjusted_score", 0.0) or 0.0),
                    diversification_value=float(ranking.get("diversification_value", 0.0) or 0.0),
                    turnover_profile=str(row.get("state") or "medium"),
                    node_count=int(latest_expression.get("node_count", 8) or 8),
                    feature_count=len(feature_set),
                    operator_count=len(operator_set),
                    formula=str(latest_expression.get("formula") or f"alpha::{alpha_id}"),
                )
            )
            if len(out) >= limit:
                break
        return out

