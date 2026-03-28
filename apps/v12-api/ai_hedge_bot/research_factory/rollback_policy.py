from __future__ import annotations

from typing import Any

from ai_hedge_bot.app.container import CONTAINER
from ai_hedge_bot.core.clock import utc_now_iso
from ai_hedge_bot.core.ids import new_cycle_id
from ai_hedge_bot.research_factory.governance_state import GovernanceStateBridge


class RollbackPolicy:
    def __init__(self) -> None:
        self.store = CONTAINER.runtime_store
        self.bridge = GovernanceStateBridge()

    def evaluate(self, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        payload = payload or {}
        model_id = payload.get('model_id') or self._latest_model_id()
        latest_review = self._latest_review(model_id)
        latest_drift = self._latest_drift(model_id)
        candidate = self._best_rollback_candidate(exclude_model_id=model_id)
        trigger_reason = []
        if latest_review and latest_review.get('decision') == 'rollback':
            trigger_reason.append('live_review_rollback')
        if latest_drift and latest_drift.get('severity') == 'high':
            trigger_reason.append('high_decay')
        should_rollback = bool(trigger_reason)
        action = 'rollback' if should_rollback else 'hold'
        row = {
            'rollback_id': f'rollback_{new_cycle_id()}',
            'created_at': utc_now_iso(),
            'model_id': model_id,
            'trigger_reason': '|'.join(trigger_reason) if trigger_reason else 'none',
            'selected_model_id': candidate.get('model_id', model_id),
            'selected_model_version': candidate.get('model_version', 'n/a'),
            'selected_score': float(candidate.get('selected_score', 0.0)),
            'action': action,
            'notes': payload.get('notes', 'phaseh sprint3 rollback evaluation'),
        }
        self.store.append('rollback_events', row)
        if action == 'rollback':
            self.bridge.transition_model(model_id, 'rolled_back', 'rollback_policy_triggered', row['created_at'])
            alpha_id = self.bridge.alpha_id_for_model(model_id)
            if alpha_id:
                self.bridge.transition_alpha(alpha_id, 'retired', 'rollback', 'rollback_policy_triggered', row['created_at'])
                self.store.append('alpha_demotions', {
                    'demotion_id': f'demotion_{new_cycle_id()}',
                    'created_at': row['created_at'],
                    'alpha_id': alpha_id,
                    'decision': 'rollback',
                    'source_run_id': row['rollback_id'],
                    'notes': 'demoted by rollback policy',
                })
        return row

    def list_latest(self, limit: int = 25) -> list[dict[str, Any]]:
        return self.store.fetchall_dict(
            """
            SELECT rollback_id, created_at, model_id, trigger_reason, selected_model_id,
                   selected_model_version, selected_score, action, notes
            FROM rollback_events
            ORDER BY created_at DESC
            LIMIT ?
            """,
            [limit],
        )

    def ensure_seed(self) -> None:
        count = self.store.fetchone_dict('SELECT COUNT(*) AS c FROM rollback_events')
        if int((count or {}).get('c') or 0) == 0:
            self.evaluate({'notes': 'seed rollback evaluation'})

    def _latest_model_id(self) -> str:
        row = self.store.fetchone_dict('SELECT model_id FROM model_registry ORDER BY created_at DESC LIMIT 1')
        return str((row or {}).get('model_id') or 'model_seed')

    def _latest_review(self, model_id: str) -> dict[str, Any] | None:
        return self.store.fetchone_dict(
            'SELECT decision FROM model_live_reviews WHERE model_id = ? ORDER BY created_at DESC LIMIT 1',
            [model_id],
        )

    def _latest_drift(self, model_id: str) -> dict[str, Any] | None:
        return self.store.fetchone_dict(
            'SELECT severity FROM alpha_drift_events WHERE model_id = ? ORDER BY created_at DESC LIMIT 1',
            [model_id],
        )

    def _best_rollback_candidate(self, exclude_model_id: str) -> dict[str, Any]:
        rows = self.store.fetchall_dict(
            """
            SELECT m.model_id, m.model_version, m.state, COALESCE(v.summary_score, 0.0) AS summary_score
            FROM model_registry m
            LEFT JOIN validation_registry v ON v.experiment_id = m.experiment_id
            WHERE m.model_id <> ?
            ORDER BY summary_score DESC, m.created_at DESC
            LIMIT 5
            """,
            [exclude_model_id],
        )
        if rows:
            best = rows[0]
            return {
                'model_id': best['model_id'],
                'model_version': best['model_version'],
                'selected_score': float(best.get('summary_score') or 0.0),
            }
        row = self.store.fetchone_dict(
            'SELECT model_id, model_version FROM model_registry ORDER BY created_at DESC LIMIT 1'
        ) or {}
        return {
            'model_id': row.get('model_id', exclude_model_id),
            'model_version': row.get('model_version', 'n/a'),
            'selected_score': 0.0,
        }
