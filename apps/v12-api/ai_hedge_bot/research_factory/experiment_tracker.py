from __future__ import annotations

from typing import Any

from ai_hedge_bot.app.container import CONTAINER
from ai_hedge_bot.core.clock import utc_now_iso
from ai_hedge_bot.core.ids import new_cycle_id
from ai_hedge_bot.research_factory.common import parse_json_field


class ExperimentTracker:
    def __init__(self) -> None:
        self.store = CONTAINER.runtime_store

    def register(self, payload: dict[str, Any]) -> dict[str, Any]:
        row = {
            'experiment_id': payload.get('experiment_id') or f'exp_{new_cycle_id()}',
            'created_at': utc_now_iso(),
            'dataset_version': payload.get('dataset_version', 'dataset.synthetic.v1'),
            'feature_version': payload.get('feature_version', 'features.core.v1'),
            'model_version': payload.get('model_version', 'model.baseline.v1'),
            'alpha_id': payload.get('alpha_id', 'alpha.synthetic.momentum'),
            'strategy_id': payload.get('strategy_id', 'trend_core'),
            'hypothesis': payload.get('hypothesis', 'Synthetic experiment registered by Sprint2 bootstrap'),
            'hyperparameters_json': self.store.to_json(payload.get('hyperparameters', {'lr': 0.05, 'depth': 4})),
            'validation_result_json': self.store.to_json(payload.get('validation_result', {'walk_forward_sharpe': 1.2, 'max_drawdown': 0.08})),
            'notes': payload.get('notes', 'immutable experiment record'),
            'immutable_record': True,
        }
        self.store.append('experiment_tracker', row)
        return self._decode(row)

    def list_latest(self, limit: int = 25) -> list[dict[str, Any]]:
        rows = self.store.fetchall_dict(
            """
            SELECT experiment_id, created_at, dataset_version, feature_version, model_version,
                   alpha_id, strategy_id, hypothesis, hyperparameters_json,
                   validation_result_json, notes, immutable_record
            FROM experiment_tracker
            ORDER BY created_at DESC
            LIMIT ?
            """,
            [limit],
        )
        return [self._decode(r) for r in rows]

    def ensure_seed(self) -> None:
        count = self.store.fetchone_dict('SELECT COUNT(*) AS c FROM experiment_tracker')
        if int((count or {}).get('c') or 0) == 0:
            self.register({})

    def _decode(self, row: dict[str, Any]) -> dict[str, Any]:
        out = dict(row)
        out['hyperparameters'] = parse_json_field(out.pop('hyperparameters_json', None), {})
        out['validation_result'] = parse_json_field(out.pop('validation_result_json', None), {})
        return out
