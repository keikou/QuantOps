from __future__ import annotations

from typing import Any

from ai_hedge_bot.app.container import CONTAINER
from ai_hedge_bot.core.clock import utc_now_iso
from ai_hedge_bot.core.ids import new_cycle_id
from ai_hedge_bot.research_factory.common import parse_json_field

ALLOWED_STATES = {'candidate', 'approved', 'live', 'shadow', 'deprecated', 'rejected', 'rolled_back'}


class ModelRegistry:
    def __init__(self) -> None:
        self.store = CONTAINER.runtime_store

    def register(self, payload: dict[str, Any]) -> dict[str, Any]:
        state = str(payload.get('state', 'candidate'))
        if state not in ALLOWED_STATES:
            state = 'candidate'
        row = {
            'model_id': payload.get('model_id') or f'model_{new_cycle_id()}',
            'created_at': utc_now_iso(),
            'experiment_id': payload.get('experiment_id'),
            'dataset_version': payload.get('dataset_version', 'dataset.synthetic.v1'),
            'feature_version': payload.get('feature_version', 'features.core.v1'),
            'model_version': payload.get('model_version', 'model.baseline.v1'),
            'validation_metrics_json': self.store.to_json(payload.get('validation_metrics', {'summary_score': 0.72, 'max_drawdown': 0.09})),
            'state': state,
            'notes': payload.get('notes', 'registered by phaseh sprint2'),
        }
        self.store.append('model_registry', row)
        self.store.append('model_state_transitions', {
            'transition_id': f'trans_{new_cycle_id()}',
            'created_at': row['created_at'],
            'model_id': row['model_id'],
            'from_state': 'none',
            'to_state': state,
            'reason': 'initial_registration',
        })
        return self._decode(row)

    def list_latest(self, limit: int = 25) -> list[dict[str, Any]]:
        rows = self.store.fetchall_dict(
            """
            SELECT model_id, created_at, experiment_id, dataset_version, feature_version,
                   model_version, validation_metrics_json, state, notes
            FROM model_registry
            ORDER BY created_at DESC
            LIMIT ?
            """,
            [limit],
        )
        return [self._decode(r) for r in rows]

    def latest_transitions(self, model_id: str | None = None, limit: int = 25) -> list[dict[str, Any]]:
        sql = """
            SELECT transition_id, created_at, model_id, from_state, to_state, reason
            FROM model_state_transitions
        """
        params: list[Any] = []
        if model_id:
            sql += ' WHERE model_id = ?'
            params.append(model_id)
        sql += ' ORDER BY created_at DESC LIMIT ?'
        params.append(limit)
        return self.store.fetchall_dict(sql, params)

    def ensure_seed(self, experiment_id: str) -> None:
        count = self.store.fetchone_dict('SELECT COUNT(*) AS c FROM model_registry')
        if int((count or {}).get('c') or 0) == 0:
            self.register({'experiment_id': experiment_id})

    def _decode(self, row: dict[str, Any]) -> dict[str, Any]:
        out = dict(row)
        out['validation_metrics'] = parse_json_field(out.pop('validation_metrics_json', None), {})
        return out
