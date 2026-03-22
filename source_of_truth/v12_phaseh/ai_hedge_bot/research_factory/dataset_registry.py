from __future__ import annotations

from typing import Any

from ai_hedge_bot.app.container import CONTAINER
from ai_hedge_bot.core.clock import utc_now_iso
from ai_hedge_bot.core.ids import new_cycle_id
from ai_hedge_bot.research_factory.common import parse_json_field


class DatasetRegistry:
    def __init__(self) -> None:
        self.store = CONTAINER.runtime_store

    def register(self, payload: dict[str, Any]) -> dict[str, Any]:
        row = {
            'dataset_id': payload.get('dataset_id') or f'ds_{new_cycle_id()}',
            'registered_at': utc_now_iso(),
            'dataset_version': payload.get('dataset_version', 'dataset.synthetic.v1'),
            'source': payload.get('source', 'synthetic-market-pipeline'),
            'symbol_scope_json': self.store.to_json(payload.get('symbol_scope', CONTAINER.config.symbols)),
            'timeframe': payload.get('timeframe', '15m'),
            'missing_rate': float(payload.get('missing_rate', 0.0)),
            'quality_summary_json': self.store.to_json(payload.get('quality_summary', {'freshness': 'ok', 'anomalies': 0})),
            'drift_summary_json': self.store.to_json(payload.get('drift_summary', {'drift_score': 0.04, 'status': 'stable'})),
            'created_by': payload.get('created_by', 'phaseh_sprint2'),
        }
        self.store.append('dataset_registry', row)
        return self._decode(row)

    def list_latest(self, limit: int = 25) -> list[dict[str, Any]]:
        rows = self.store.fetchall_dict(
            """
            SELECT dataset_id, registered_at, dataset_version, source, symbol_scope_json,
                   timeframe, missing_rate, quality_summary_json, drift_summary_json, created_by
            FROM dataset_registry
            ORDER BY registered_at DESC
            LIMIT ?
            """,
            [limit],
        )
        return [self._decode(r) for r in rows]

    def ensure_seed(self) -> None:
        count = self.store.fetchone_dict('SELECT COUNT(*) AS c FROM dataset_registry')
        if int((count or {}).get('c') or 0) == 0:
            self.register({})

    def _decode(self, row: dict[str, Any]) -> dict[str, Any]:
        out = dict(row)
        out['symbol_scope'] = parse_json_field(out.pop('symbol_scope_json', None), [])
        out['quality_summary'] = parse_json_field(out.pop('quality_summary_json', None), {})
        out['drift_summary'] = parse_json_field(out.pop('drift_summary_json', None), {})
        return out
