from __future__ import annotations

from typing import Any

from ai_hedge_bot.app.container import CONTAINER
from ai_hedge_bot.core.clock import utc_now_iso
from ai_hedge_bot.core.ids import new_cycle_id
from ai_hedge_bot.research_factory.common import parse_json_field
from ai_hedge_bot.research_factory.governance_state import GovernanceStateBridge


class LiveModelReview:
    def __init__(self) -> None:
        self.store = CONTAINER.runtime_store
        self.bridge = GovernanceStateBridge()

    def evaluate(self, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        payload = payload or {}
        model_id = payload.get('model_id') or self._latest_model_id()
        strategy = self._latest_strategy_metrics()
        execution = self._latest_execution_metrics()
        thresholds = {
            'pnl_drift_alert': float(payload.get('pnl_drift_alert', 0.08)),
            'slippage_alert_bps': float(payload.get('slippage_alert_bps', 12.0)),
            'fill_rate_floor': float(payload.get('fill_rate_floor', 0.82)),
            'drawdown_alert': float(payload.get('drawdown_alert', 0.12)),
        }
        pnl_drift = max(0.0, float(strategy.get('expected_return', 0.0)) - float(strategy.get('realized_return', 0.0)))
        hit_rate = float(strategy.get('hit_rate', 0.0))
        turnover = float(strategy.get('turnover', 0.0))
        drawdown = abs(float(strategy.get('drawdown', 0.0)))
        slippage = float(execution.get('avg_slippage_bps', 0.0))
        fill_rate = float(execution.get('fill_rate', 0.0))
        flags: list[str] = []
        if pnl_drift > thresholds['pnl_drift_alert']:
            flags.append('pnl_drift')
        if slippage > thresholds['slippage_alert_bps']:
            flags.append('slippage_drift')
        if fill_rate < thresholds['fill_rate_floor']:
            flags.append('fill_rate_weak')
        if drawdown > thresholds['drawdown_alert']:
            flags.append('drawdown_breach')
        if hit_rate < 0.5:
            flags.append('hit_rate_weak')
        action = 'keep'
        if {'drawdown_breach', 'slippage_drift'} & set(flags):
            action = 'rollback'
        elif {'pnl_drift', 'fill_rate_weak'} & set(flags):
            action = 'reduce_capital'
        elif 'hit_rate_weak' in flags:
            action = 'shadow'
        record = {
            'review_id': f'review_{new_cycle_id()}',
            'created_at': utc_now_iso(),
            'model_id': model_id,
            'strategy_id': strategy.get('strategy_id', 'trend_core'),
            'decision': action,
            'pnl_drift': pnl_drift,
            'hit_rate': hit_rate,
            'slippage_bps': slippage,
            'fill_rate': fill_rate,
            'turnover': turnover,
            'risk_usage': float(payload.get('risk_usage', 0.64)),
            'flags_json': self.store.to_json(flags),
            'notes': payload.get('notes', 'phaseh sprint3 live review'),
        }
        self.store.append('model_live_reviews', record)
        model_target, alpha_target = self._governance_targets(action)
        if model_target:
            self.bridge.transition_model(model_id, model_target, f'live_review_{action}', record['created_at'])
        alpha_id = self.bridge.alpha_id_for_model(model_id)
        if alpha_id and alpha_target:
            self.bridge.transition_alpha(alpha_id, alpha_target, 'live_review', f'live_review_{action}', record['created_at'])
        return self._decode(record)

    def list_latest(self, limit: int = 25) -> list[dict[str, Any]]:
        rows = self.store.fetchall_dict(
            """
            SELECT review_id, created_at, model_id, strategy_id, decision, pnl_drift,
                   hit_rate, slippage_bps, fill_rate, turnover, risk_usage, flags_json, notes
            FROM model_live_reviews
            ORDER BY created_at DESC
            LIMIT ?
            """,
            [limit],
        )
        return [self._decode(r) for r in rows]

    def ensure_seed(self) -> None:
        count = self.store.fetchone_dict('SELECT COUNT(*) AS c FROM model_live_reviews')
        if int((count or {}).get('c') or 0) == 0:
            self.evaluate({'notes': 'seed live review'})

    def _latest_model_id(self) -> str:
        row = self.store.fetchone_dict('SELECT model_id FROM model_registry ORDER BY created_at DESC LIMIT 1')
        return str((row or {}).get('model_id') or 'model_seed')

    def _latest_strategy_metrics(self) -> dict[str, Any]:
        row = self.store.fetchone_dict(
            """
            SELECT strategy_id, expected_return, realized_return, hit_rate, turnover, drawdown
            FROM strategy_performance_daily
            ORDER BY created_at DESC LIMIT 1
            """
        )
        if row:
            return row
        return {
            'strategy_id': 'trend_core',
            'expected_return': 0.11,
            'realized_return': 0.07,
            'hit_rate': 0.56,
            'turnover': 0.38,
            'drawdown': -0.06,
        }

    def _latest_execution_metrics(self) -> dict[str, Any]:
        row = self.store.fetchone_dict(
            """
            SELECT avg_slippage_bps, fill_rate
            FROM execution_quality_snapshots
            ORDER BY created_at DESC LIMIT 1
            """
        )
        if row:
            return row
        return {'avg_slippage_bps': 6.0, 'fill_rate': 0.9}

    def _decode(self, row: dict[str, Any]) -> dict[str, Any]:
        out = dict(row)
        out['flags'] = parse_json_field(out.pop('flags_json', None), [])
        return out

    def _governance_targets(self, action: str) -> tuple[str | None, str | None]:
        if action == 'keep':
            return 'live', 'promoted'
        if action == 'reduce_capital':
            return 'approved', 'monitor'
        if action == 'shadow':
            return 'shadow', 'shadow'
        if action == 'rollback':
            return 'shadow', 'review_required'
        return None, None
