from __future__ import annotations

from typing import Any

from ai_hedge_bot.app.container import CONTAINER
from ai_hedge_bot.core.ids import new_cycle_id
from ai_hedge_bot.learning.champion_challenger import ChampionChallenger
from ai_hedge_bot.repositories.audit_repository import AuditRepository
from ai_hedge_bot.research_factory.alpha_decay_monitor import AlphaDecayMonitor
from ai_hedge_bot.research_factory.dataset_registry import DatasetRegistry
from ai_hedge_bot.research_factory.experiment_tracker import ExperimentTracker
from ai_hedge_bot.research_factory.feature_registry import FeatureRegistry
from ai_hedge_bot.research_factory.live_model_review import LiveModelReview
from ai_hedge_bot.research_factory.model_registry import ModelRegistry
from ai_hedge_bot.research_factory.promotion_policy import PromotionPolicy
from ai_hedge_bot.research_factory.rollback_policy import RollbackPolicy
from ai_hedge_bot.research_factory.validation_registry import ValidationRegistry


class ResearchFactoryService:
    def __init__(self) -> None:
        self.audit_repo = AuditRepository()
        self.experiments = ExperimentTracker()
        self.datasets = DatasetRegistry()
        self.features = FeatureRegistry()
        self.validations = ValidationRegistry()
        self.models = ModelRegistry()
        self.promotions = PromotionPolicy()
        self.live_reviews = LiveModelReview()
        self.decay_monitor = AlphaDecayMonitor()
        self.rollback_policy = RollbackPolicy()
        self.champion_challenger = ChampionChallenger()
        self._ensure_seed_data()

    def _audit_actor(self, payload: dict[str, Any]) -> str:
        for key in ("actor", "created_by", "requested_by"):
            value = str(payload.get(key) or "").strip()
            if value:
                return value
        return "research_factory_api"

    def _mirror_registration_audit(
        self,
        *,
        event_type: str,
        actor: str,
        payload: dict[str, Any],
    ) -> None:
        self.audit_repo.create_log(
            {
                "audit_id": new_cycle_id(),
                "category": "research_factory",
                "event_type": event_type,
                "run_id": None,
                "created_at": str(payload.get("created_at") or payload.get("registered_at") or ""),
                "payload_json": CONTAINER.runtime_store.to_json(payload),
                "actor": actor,
            }
        )

    def _ensure_seed_data(self) -> None:
        self.datasets.ensure_seed()
        self.features.ensure_seed()
        self.experiments.ensure_seed()
        latest_experiment = self.experiments.list_latest(limit=1)[0]
        self.validations.ensure_seed(latest_experiment['experiment_id'])
        self.models.ensure_seed(latest_experiment['experiment_id'])
        self.promotions.ensure_seed()
        self.live_reviews.ensure_seed()
        self.decay_monitor.ensure_seed()
        self.rollback_policy.ensure_seed()
        self.champion_challenger.ensure_seed()

    def register_experiment(self, payload: dict[str, Any]) -> dict[str, Any]:
        row = self.experiments.register(payload)
        self._mirror_registration_audit(
            event_type="experiment_registered",
            actor=self._audit_actor(payload),
            payload={
                "experiment_id": row["experiment_id"],
                "dataset_version": row["dataset_version"],
                "feature_version": row["feature_version"],
                "model_version": row["model_version"],
                "alpha_id": row["alpha_id"],
                "strategy_id": row["strategy_id"],
                "immutable_record": row["immutable_record"],
                "created_at": row["created_at"],
            },
        )
        return {'status': 'ok', 'experiment': row}

    def register_dataset(self, payload: dict[str, Any]) -> dict[str, Any]:
        row = self.datasets.register(payload)
        self._mirror_registration_audit(
            event_type="dataset_registered",
            actor=self._audit_actor(payload),
            payload={
                "dataset_id": row["dataset_id"],
                "dataset_version": row["dataset_version"],
                "source": row["source"],
                "timeframe": row["timeframe"],
                "created_by": row["created_by"],
                "registered_at": row["registered_at"],
            },
        )
        return {'status': 'ok', 'dataset': row}

    def register_feature(self, payload: dict[str, Any]) -> dict[str, Any]:
        row = self.features.register(payload)
        self._mirror_registration_audit(
            event_type="feature_registered",
            actor=self._audit_actor(payload),
            payload={
                "feature_id": row["feature_id"],
                "feature_version": row["feature_version"],
                "feature_count": len(row["feature_list"]),
                "created_by": row["created_by"],
                "registered_at": row["registered_at"],
            },
        )
        return {'status': 'ok', 'feature': row}

    def register_validation(self, payload: dict[str, Any]) -> dict[str, Any]:
        if not payload.get('experiment_id'):
            latest = self.experiments.list_latest(limit=1)[0]
            payload = {**payload, 'experiment_id': latest['experiment_id']}
        row = self.validations.register(payload)
        self._mirror_registration_audit(
            event_type="validation_registered",
            actor=self._audit_actor(payload),
            payload={
                "validation_id": row["validation_id"],
                "experiment_id": row["experiment_id"],
                "summary_score": row["summary_score"],
                "passed": row["passed"],
                "created_at": row["created_at"],
            },
        )
        return {'status': 'ok', 'validation': row}

    def register_model(self, payload: dict[str, Any]) -> dict[str, Any]:
        if not payload.get('experiment_id'):
            latest = self.experiments.list_latest(limit=1)[0]
            payload = {**payload, 'experiment_id': latest['experiment_id']}
        row = self.models.register(payload)
        self._mirror_registration_audit(
            event_type="model_registered",
            actor=self._audit_actor(payload),
            payload={
                "model_id": row["model_id"],
                "experiment_id": row["experiment_id"],
                "dataset_version": row["dataset_version"],
                "feature_version": row["feature_version"],
                "model_version": row["model_version"],
                "state": row["state"],
                "created_at": row["created_at"],
            },
        )
        return {'status': 'ok', 'model': row, 'transitions': self.models.latest_transitions(row['model_id'], limit=5)}

    def evaluate_promotion(self, payload: dict[str, Any]) -> dict[str, Any]:
        row = self.promotions.evaluate(payload)
        self._mirror_registration_audit(
            event_type="promotion_evaluated",
            actor=self._audit_actor(payload),
            payload={
                "evaluation_id": row["evaluation_id"],
                "model_id": row["model_id"],
                "experiment_id": row["experiment_id"],
                "decision": row["decision"],
                "summary_score": row["summary_score"],
                "cost_adjusted_score": row["cost_adjusted_score"],
                "created_at": row["created_at"],
            },
        )
        return {'status': 'ok', 'promotion': row}

    def latest_live_review(self, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        row = self.live_reviews.evaluate(payload or {})
        self._mirror_registration_audit(
            event_type="live_review_evaluated",
            actor=self._audit_actor(payload or {}),
            payload={
                "review_id": row["review_id"],
                "model_id": row["model_id"],
                "strategy_id": row["strategy_id"],
                "decision": row["decision"],
                "pnl_drift": row["pnl_drift"],
                "fill_rate": row["fill_rate"],
                "created_at": row["created_at"],
            },
        )
        return {'status': 'ok', 'review': row}

    def latest_alpha_decay(self, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        row = self.decay_monitor.evaluate(payload or {})
        self._mirror_registration_audit(
            event_type="alpha_decay_evaluated",
            actor=self._audit_actor(payload or {}),
            payload={
                "event_id": row["event_id"],
                "model_id": row["model_id"],
                "alpha_id": row["alpha_id"],
                "severity": row["severity"],
                "status": row["status"],
                "symbol": row["symbol"],
                "created_at": row["created_at"],
            },
        )
        return {'status': 'ok', 'decay': row}

    def evaluate_rollback(self, payload: dict[str, Any]) -> dict[str, Any]:
        row = self.rollback_policy.evaluate(payload)
        self._mirror_registration_audit(
            event_type="rollback_evaluated",
            actor=self._audit_actor(payload),
            payload={
                "rollback_id": row["rollback_id"],
                "model_id": row["model_id"],
                "selected_model_id": row["selected_model_id"],
                "action": row["action"],
                "trigger_reason": row["trigger_reason"],
                "created_at": row["created_at"],
            },
        )
        return {'status': 'ok', 'rollback': row}

    def run_champion_challenger(self, payload: dict[str, Any]) -> dict[str, Any]:
        row = self.champion_challenger.run(payload)
        self._mirror_registration_audit(
            event_type="champion_challenger_run",
            actor=self._audit_actor(payload),
            payload={
                "run_id": row["run_id"],
                "champion_model_id": row["champion_model_id"],
                "challenger_model_id": row["challenger_model_id"],
                "winner": row["winner"],
                "recommended_action": row["recommended_action"],
                "capital_shift": row["capital_shift"],
                "created_at": row["created_at"],
            },
        )
        return {'status': 'ok', 'run': row}

    def governance_overview(self) -> dict[str, Any]:
        promotions = self.promotions.list_latest(10)
        reviews = self.live_reviews.list_latest(10)
        decay = self.decay_monitor.list_latest(10)
        rollbacks = self.rollback_policy.list_latest(10)
        cc_runs = self.champion_challenger.list_latest(10)
        decision_counts: dict[str, int] = {}
        for row in promotions:
            k = str(row.get('decision', 'unknown'))
            decision_counts[k] = decision_counts.get(k, 0) + 1
        live_decisions: dict[str, int] = {}
        for row in reviews:
            k = str(row.get('decision', 'unknown'))
            live_decisions[k] = live_decisions.get(k, 0) + 1
        decay_counts: dict[str, int] = {}
        for row in decay:
            k = str(row.get('severity', 'unknown'))
            decay_counts[k] = decay_counts.get(k, 0) + 1
        return {
            'status': 'ok',
            'promotion_decisions': decision_counts,
            'live_review_decisions': live_decisions,
            'decay_severity': decay_counts,
            'latest_promotion': promotions[0] if promotions else None,
            'latest_live_review': reviews[0] if reviews else None,
            'latest_decay': decay[0] if decay else None,
            'latest_rollback': rollbacks[0] if rollbacks else None,
            'latest_champion_challenger': cc_runs[0] if cc_runs else None,
            'promotions': promotions,
            'live_reviews': reviews,
            'decay_events': decay,
            'rollback_events': rollbacks,
            'champion_challenger_runs': cc_runs,
        }

    def overview(self) -> dict[str, Any]:
        experiments = self.experiments.list_latest()
        datasets = self.datasets.list_latest()
        features = self.features.list_latest()
        validations = self.validations.list_latest()
        models = self.models.list_latest()
        counts = {
            'experiments': len(experiments),
            'datasets': len(datasets),
            'features': len(features),
            'validations': len(validations),
            'models': len(models),
        }
        state_counts: dict[str, int] = {}
        for model in models:
            state = str(model.get('state', 'unknown'))
            state_counts[state] = state_counts.get(state, 0) + 1
        governance = self.governance_overview()
        return {
            'status': 'ok',
            'counts': counts,
            'state_counts': state_counts,
            'latest_experiment': experiments[0] if experiments else None,
            'latest_model': models[0] if models else None,
            'latest_validation': validations[0] if validations else None,
            'governance': {
                'promotion_decisions': governance.get('promotion_decisions', {}),
                'live_review_decisions': governance.get('live_review_decisions', {}),
                'decay_severity': governance.get('decay_severity', {}),
            },
            'experiments': experiments,
            'datasets': datasets,
            'features': features,
            'validations': validations,
            'models': models,
        }
