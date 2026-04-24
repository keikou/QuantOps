from __future__ import annotations

from ai_hedge_bot.app.container import CONTAINER
from ai_hedge_bot.alpha_synthesis.dsl.expression import AlphaExpression
from ai_hedge_bot.core.clock import utc_now_iso
from ai_hedge_bot.core.ids import new_cycle_id


class AlphaSynthesisAAEBridge:
    def __init__(self) -> None:
        self.store = CONTAINER.runtime_store

    def submit(self, expression_id: str, expr: AlphaExpression) -> dict:
        existing = self.store.fetchone_dict(
            """
            SELECT *
            FROM alpha_registry
            WHERE notes=?
            ORDER BY created_at DESC
            LIMIT 1
            """,
            [f"asd01:{expression_id}"],
        )
        if existing:
            return {
                "aae_submission_status": "already_submitted",
                "alpha_id": existing.get("alpha_id"),
            }

        created_at = utc_now_iso()
        alpha_id = f"asd.{expression_id}"
        self.store.append(
            "alpha_registry",
            {
                "alpha_id": alpha_id,
                "created_at": created_at,
                "alpha_family": "synthesized",
                "factor_type": "symbolic",
                "horizon": "short",
                "turnover_profile": "medium",
                "feature_dependencies_json": self.store.to_json(expr.feature_set),
                "risk_profile": "balanced",
                "execution_sensitivity": 0.25,
                "state": "candidate",
                "source": "alpha_synthesis_asd01",
                "notes": f"asd01:{expression_id}",
            }
        )
        self.store.append(
            "alpha_experiments",
            {
                "experiment_id": new_cycle_id(),
                "created_at": created_at,
                "alpha_id": alpha_id,
                "generation_theme": "symbolic_alpha_synthesis",
                "design_json": self.store.to_json({"expression_id": expression_id, "formula": expr.formula}),
                "status": "generated",
                "notes": "asd01_expression_submitted_to_aae",
            }
        )
        return {"aae_submission_status": "submitted_to_aae", "alpha_id": alpha_id}

