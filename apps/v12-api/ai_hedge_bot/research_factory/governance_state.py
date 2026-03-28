from __future__ import annotations

from typing import Any

from ai_hedge_bot.app.container import CONTAINER
from ai_hedge_bot.core.ids import new_cycle_id


class GovernanceStateBridge:
    def __init__(self) -> None:
        self.store = CONTAINER.runtime_store

    def transition_model(self, model_id: str, to_state: str, reason: str, created_at: str) -> bool:
        latest = self.store.fetchone_dict(
            """
            SELECT model_id, experiment_id, dataset_version, feature_version, model_version,
                   validation_metrics_json, state, notes
            FROM model_registry
            WHERE model_id = ?
            ORDER BY created_at DESC
            LIMIT 1
            """,
            [model_id],
        )
        if not latest:
            return False
        from_state = str(latest.get("state") or "candidate")
        if from_state == to_state:
            return False
        self.store.append(
            "model_registry",
            {
                "model_id": model_id,
                "created_at": created_at,
                "experiment_id": latest.get("experiment_id"),
                "dataset_version": latest.get("dataset_version"),
                "feature_version": latest.get("feature_version"),
                "model_version": latest.get("model_version"),
                "validation_metrics_json": latest.get("validation_metrics_json") or "{}",
                "state": to_state,
                "notes": reason,
            },
        )
        self.store.append(
            "model_state_transitions",
            {
                "transition_id": f"trans_{new_cycle_id()}",
                "created_at": created_at,
                "model_id": model_id,
                "from_state": from_state,
                "to_state": to_state,
                "reason": reason,
            },
        )
        return True

    def transition_alpha(
        self,
        alpha_id: str,
        to_state: str,
        event_type: str,
        reason: str,
        created_at: str,
    ) -> bool:
        alpha = self.store.fetchone_dict(
            """
            SELECT alpha_id, alpha_family, factor_type, horizon, turnover_profile,
                   feature_dependencies_json, risk_profile, execution_sensitivity,
                   state, source, notes
            FROM alpha_registry
            WHERE alpha_id = ?
            ORDER BY created_at DESC
            LIMIT 1
            """,
            [alpha_id],
        )
        library = self.store.fetchone_dict(
            """
            SELECT alpha_family, factor_type, state, rank_score, usage_count, tags_json
            FROM alpha_library
            WHERE alpha_id = ?
            ORDER BY created_at DESC
            LIMIT 1
            """,
            [alpha_id],
        )
        if not alpha:
            return False
        from_state = str((library or alpha).get("state") or alpha.get("state") or "candidate")
        if from_state == to_state:
            return False
        self.store.append(
            "alpha_registry",
            {
                "alpha_id": alpha_id,
                "created_at": created_at,
                "alpha_family": alpha.get("alpha_family"),
                "factor_type": alpha.get("factor_type"),
                "horizon": alpha.get("horizon"),
                "turnover_profile": alpha.get("turnover_profile"),
                "feature_dependencies_json": alpha.get("feature_dependencies_json") or "[]",
                "risk_profile": alpha.get("risk_profile"),
                "execution_sensitivity": float(alpha.get("execution_sensitivity") or 0.0),
                "state": to_state,
                "source": "governance_state_bridge",
                "notes": reason,
            },
        )
        self.store.append(
            "alpha_library",
            {
                "library_id": new_cycle_id(),
                "created_at": created_at,
                "alpha_id": alpha_id,
                "alpha_family": (library or alpha).get("alpha_family"),
                "factor_type": (library or alpha).get("factor_type"),
                "state": to_state,
                "rank_score": float((library or {}).get("rank_score") or 0.0),
                "usage_count": int((library or {}).get("usage_count") or 0),
                "tags_json": (library or {}).get("tags_json") or "[]",
            },
        )
        self.store.append(
            "alpha_status_events",
            {
                "event_id": new_cycle_id(),
                "created_at": created_at,
                "alpha_id": alpha_id,
                "event_type": event_type,
                "from_state": from_state,
                "to_state": to_state,
                "reason": reason,
            },
        )
        return True

    def alpha_id_for_model(self, model_id: str) -> str | None:
        row = self.store.fetchone_dict(
            """
            SELECT e.alpha_id
            FROM model_registry m
            JOIN experiment_tracker e ON e.experiment_id = m.experiment_id
            WHERE m.model_id = ?
            ORDER BY m.created_at DESC, e.created_at DESC
            LIMIT 1
            """,
            [model_id],
        )
        alpha_id = str((row or {}).get("alpha_id") or "").strip()
        return alpha_id or None
