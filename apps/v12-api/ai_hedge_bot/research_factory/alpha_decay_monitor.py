from __future__ import annotations

from typing import Any

from ai_hedge_bot.app.container import CONTAINER
from ai_hedge_bot.core.clock import utc_now_iso
from ai_hedge_bot.core.ids import new_cycle_id
from ai_hedge_bot.research_factory.common import parse_json_field
from ai_hedge_bot.research_factory.governance_state import GovernanceStateBridge


class AlphaDecayMonitor:
    def __init__(self) -> None:
        self.store = CONTAINER.runtime_store
        self.bridge = GovernanceStateBridge()

    def evaluate(self, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        payload = payload or {}
        model_id = payload.get('model_id') or self._latest_model_id()
        alpha_id = payload.get('alpha_id') or self._latest_alpha_id()
        rolling_ic = float(payload.get('rolling_ic', 0.048))
        baseline_ic = float(payload.get('baseline_ic', 0.082))
        hit_rate_now = float(payload.get('hit_rate_now', 0.53))
        hit_rate_baseline = float(payload.get('hit_rate_baseline', 0.61))
        score_now = float(payload.get('summary_score_now', 0.69))
        score_baseline = float(payload.get('summary_score_baseline', 0.79))
        regime = payload.get('regime', 'trend_up')
        symbol = payload.get('symbol', 'BTCUSDT')
        ic_drop = max(0.0, baseline_ic - rolling_ic)
        hit_rate_drop = max(0.0, hit_rate_baseline - hit_rate_now)
        score_drop = max(0.0, score_baseline - score_now)
        severity = 'stable'
        if score_drop >= 0.14 or ic_drop >= 0.05:
            severity = 'high'
        elif score_drop >= 0.08 or ic_drop >= 0.025 or hit_rate_drop >= 0.05:
            severity = 'medium'
        flags: list[str] = []
        if ic_drop >= 0.025:
            flags.append('ic_decay')
        if hit_rate_drop >= 0.05:
            flags.append('hit_rate_decay')
        if score_drop >= 0.08:
            flags.append('score_decay')
        status = 'monitor'
        if severity == 'high':
            status = 'demote_candidate'
        elif severity == 'medium':
            status = 'review_required'
        record = {
            'event_id': f'drift_{new_cycle_id()}',
            'created_at': utc_now_iso(),
            'model_id': model_id,
            'alpha_id': alpha_id,
            'symbol': symbol,
            'regime': regime,
            'rolling_ic': rolling_ic,
            'hit_rate_now': hit_rate_now,
            'summary_score_now': score_now,
            'severity': severity,
            'status': status,
            'flags_json': self.store.to_json(flags),
            'notes': payload.get('notes', 'phaseh sprint3 decay monitor'),
        }
        self.store.append('alpha_drift_events', record)
        alpha_target = self._alpha_target_state(status)
        if alpha_target:
            self.bridge.transition_alpha(alpha_id, alpha_target, 'decay', f'alpha_decay_{status}', record['created_at'])
        return self._decode(record)

    def list_latest(self, limit: int = 25) -> list[dict[str, Any]]:
        rows = self.store.fetchall_dict(
            """
            SELECT event_id, created_at, model_id, alpha_id, symbol, regime, rolling_ic,
                   hit_rate_now, summary_score_now, severity, status, flags_json, notes
            FROM alpha_drift_events
            ORDER BY created_at DESC
            LIMIT ?
            """,
            [limit],
        )
        return [self._decode(r) for r in rows]

    def ensure_seed(self) -> None:
        count = self.store.fetchone_dict('SELECT COUNT(*) AS c FROM alpha_drift_events')
        if int((count or {}).get('c') or 0) == 0:
            self.evaluate({'notes': 'seed decay event'})

    def _latest_model_id(self) -> str:
        row = self.store.fetchone_dict('SELECT model_id FROM model_registry ORDER BY created_at DESC LIMIT 1')
        return str((row or {}).get('model_id') or 'model_seed')

    def _latest_alpha_id(self) -> str:
        row = self.store.fetchone_dict('SELECT alpha_id FROM experiment_tracker ORDER BY created_at DESC LIMIT 1')
        return str((row or {}).get('alpha_id') or 'alpha_seed')

    def _decode(self, row: dict[str, Any]) -> dict[str, Any]:
        out = dict(row)
        out['flags'] = parse_json_field(out.pop('flags_json', None), [])
        return out

    def _alpha_target_state(self, status: str) -> str | None:
        if status == 'review_required':
            return 'review_required'
        if status == 'demote_candidate':
            return 'demote_candidate'
        return None
