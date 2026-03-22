from __future__ import annotations

from typing import Any

from ai_hedge_bot.app.container import CONTAINER
from ai_hedge_bot.core.clock import utc_now_iso
from ai_hedge_bot.core.ids import new_cycle_id
from ai_hedge_bot.research_factory.common import parse_json_field


class FeatureRegistry:
    def __init__(self) -> None:
        self.store = CONTAINER.runtime_store

    def register(self, payload: dict[str, Any]) -> dict[str, Any]:
        feature_list = payload.get('feature_list', ['momentum_4', 'funding_zscore', 'oi_delta', 'spread_bps'])
        row = {
            'feature_id': payload.get('feature_id') or f'feat_{new_cycle_id()}',
            'registered_at': utc_now_iso(),
            'feature_version': payload.get('feature_version', 'features.core.v1'),
            'feature_list_json': self.store.to_json(feature_list),
            'transform_config_json': self.store.to_json(payload.get('transform_config', {'winsorize': True, 'clip': 5.0})),
            'normalization_config_json': self.store.to_json(payload.get('normalization_config', {'method': 'zscore'})),
            'compatibility_info_json': self.store.to_json(payload.get('compatibility_info', {'dataset_versions': ['dataset.synthetic.v1'], 'alpha_families': ['trend', 'mean_reversion']})),
            'created_by': payload.get('created_by', 'phaseh_sprint2'),
        }
        self.store.append('feature_registry', row)
        return self._decode(row)

    def list_latest(self, limit: int = 25) -> list[dict[str, Any]]:
        rows = self.store.fetchall_dict(
            """
            SELECT feature_id, registered_at, feature_version, feature_list_json,
                   transform_config_json, normalization_config_json, compatibility_info_json,
                   created_by
            FROM feature_registry
            ORDER BY registered_at DESC
            LIMIT ?
            """,
            [limit],
        )
        return [self._decode(r) for r in rows]

    def ensure_seed(self) -> None:
        count = self.store.fetchone_dict('SELECT COUNT(*) AS c FROM feature_registry')
        if int((count or {}).get('c') or 0) == 0:
            self.register({})

    def _decode(self, row: dict[str, Any]) -> dict[str, Any]:
        out = dict(row)
        out['feature_list'] = parse_json_field(out.pop('feature_list_json', None), [])
        out['transform_config'] = parse_json_field(out.pop('transform_config_json', None), {})
        out['normalization_config'] = parse_json_field(out.pop('normalization_config_json', None), {})
        out['compatibility_info'] = parse_json_field(out.pop('compatibility_info_json', None), {})
        return out
