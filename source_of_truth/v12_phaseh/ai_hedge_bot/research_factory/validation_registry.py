from __future__ import annotations

from typing import Any

from ai_hedge_bot.app.container import CONTAINER
from ai_hedge_bot.core.clock import utc_now_iso
from ai_hedge_bot.core.ids import new_cycle_id
from ai_hedge_bot.research_factory.common import parse_json_field


class ValidationRegistry:
    def __init__(self) -> None:
        self.store = CONTAINER.runtime_store

    def register(self, payload: dict[str, Any]) -> dict[str, Any]:
        row = {
            'validation_id': payload.get('validation_id') or f'val_{new_cycle_id()}',
            'created_at': utc_now_iso(),
            'experiment_id': payload.get('experiment_id'),
            'walk_forward_result_json': self.store.to_json(payload.get('walk_forward_result', {'sharpe': 1.25, 'turnover': 0.32})),
            'purged_cv_result_json': self.store.to_json(payload.get('purged_cv_result', {'auc': 0.58, 'stability': 0.91})),
            'robustness_result_json': self.store.to_json(payload.get('robustness_result', {'regime_coverage': 0.78})),
            'stress_result_json': self.store.to_json(payload.get('stress_result', {'panic_drawdown': 0.11})),
            'summary_score': float(payload.get('summary_score', 0.72)),
            'passed': bool(payload.get('passed', True)),
        }
        self.store.append('validation_registry', row)
        return self._decode(row)

    def list_latest(self, limit: int = 25) -> list[dict[str, Any]]:
        rows = self.store.fetchall_dict(
            """
            SELECT validation_id, created_at, experiment_id, walk_forward_result_json,
                   purged_cv_result_json, robustness_result_json, stress_result_json,
                   summary_score, passed
            FROM validation_registry
            ORDER BY created_at DESC
            LIMIT ?
            """,
            [limit],
        )
        return [self._decode(r) for r in rows]

    def ensure_seed(self, experiment_id: str) -> None:
        count = self.store.fetchone_dict('SELECT COUNT(*) AS c FROM validation_registry')
        if int((count or {}).get('c') or 0) == 0:
            self.register({'experiment_id': experiment_id})

    def _decode(self, row: dict[str, Any]) -> dict[str, Any]:
        out = dict(row)
        out['walk_forward_result'] = parse_json_field(out.pop('walk_forward_result_json', None), {})
        out['purged_cv_result'] = parse_json_field(out.pop('purged_cv_result_json', None), {})
        out['robustness_result'] = parse_json_field(out.pop('robustness_result_json', None), {})
        out['stress_result'] = parse_json_field(out.pop('stress_result_json', None), {})
        return out
