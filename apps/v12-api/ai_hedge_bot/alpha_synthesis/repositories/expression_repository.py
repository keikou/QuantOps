from __future__ import annotations

from ai_hedge_bot.app.container import CONTAINER
from ai_hedge_bot.alpha_synthesis.dsl.expression import AlphaExpression, from_json, to_json
from ai_hedge_bot.core.clock import utc_now_iso


class ExpressionRepository:
    def __init__(self) -> None:
        self.store = CONTAINER.runtime_store

    def insert_expression(self, expression_id: str, expr: AlphaExpression, metadata: dict) -> str:
        now = utc_now_iso()
        self.store.append(
            "alpha_expression_library",
            {
                "expression_id": expression_id,
                "expression_hash": expr.expression_hash,
                "formula": expr.formula,
                "ast_json": self.store.to_json(to_json(expr)),
                "depth": expr.depth,
                "node_count": expr.node_count,
                "feature_set_json": self.store.to_json(expr.feature_set),
                "operator_set_json": self.store.to_json(expr.operator_set),
                "generator_type": metadata.get("generator_type", "random"),
                "parent_expression_ids_json": self.store.to_json(metadata.get("parent_expression_ids") or []),
                "status": metadata.get("status", "generated"),
                "created_at": now,
                "updated_at": now,
            },
        )
        return expression_id

    def find_by_hash(self, expression_hash: str) -> AlphaExpression | None:
        row = self.store.fetchone_dict(
            """
            SELECT *
            FROM alpha_expression_library
            WHERE expression_hash=?
            ORDER BY created_at DESC
            LIMIT 1
            """,
            [expression_hash],
        )
        if not row:
            return None
        return from_json(self.store.parse_json(row.get("ast_json")))

    def list_recent_expressions(self, limit: int = 100) -> list[dict]:
        rows = self.store.fetchall_dict(
            """
            SELECT *
            FROM alpha_expression_library
            ORDER BY created_at DESC, expression_id ASC
            LIMIT ?
            """,
            [max(int(limit), 1)],
        )
        for row in rows:
            row["feature_set"] = self.store.parse_json(row.get("feature_set_json")) if row.get("feature_set_json") else []
            row["operator_set"] = self.store.parse_json(row.get("operator_set_json")) if row.get("operator_set_json") else []
            row["parent_expression_ids"] = self.store.parse_json(row.get("parent_expression_ids_json")) if row.get("parent_expression_ids_json") else []
        return rows

    def update_expression_status(self, expression_id: str, status: str) -> None:
        self.store.execute(
            """
            UPDATE alpha_expression_library
            SET status=?, updated_at=?
            WHERE expression_id=?
            """,
            [status, utc_now_iso(), expression_id],
        )

