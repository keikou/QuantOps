from __future__ import annotations

from typing import Any

from ai_hedge_bot.app.container import CONTAINER
from ai_hedge_bot.core.clock import utc_now_iso
from ai_hedge_bot.core.ids import new_cycle_id
from ai_hedge_bot.research_factory.common import parse_json_field


class PromotionPolicy:
    def __init__(self) -> None:
        self.store = CONTAINER.runtime_store

    def evaluate(self, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        payload = payload or {}
        model = self._candidate_model(payload.get('model_id'))
        validation = self._validation_for_model(model)
        strategy = self._latest_strategy_metrics()
        thresholds = {
            'promotion_score_min': float(payload.get('promotion_score_min', 0.75)),
            'sample_size_min': int(payload.get('sample_size_min', 100)),
            'drawdown_max': float(payload.get('drawdown_max', 0.12)),
            'slippage_cap_bps': float(payload.get('slippage_cap_bps', 10.0)),
        }
        summary_score = float(validation.get('summary_score', 0.0))
        max_drawdown = self._metric_from_model(model, 'max_drawdown', abs(float(strategy.get('drawdown', 0.0))))
        sample_size = int(payload.get('sample_size', 144))
        slippage = self._latest_slippage()
        regime_coverage = float(payload.get('regime_coverage', 0.85))
        cost_adjusted_score = round(summary_score - max(0.0, slippage - 4.0) / 100.0, 6)
        reasons: list[str] = []
        decision = 'approve'
        if sample_size < thresholds['sample_size_min']:
            decision = 'needs_review'
            reasons.append('insufficient_sample')
        if max_drawdown > thresholds['drawdown_max']:
            decision = 'reject'
            reasons.append('drawdown_breach')
        if slippage > thresholds['slippage_cap_bps']:
            decision = 'needs_review' if decision != 'reject' else decision
            reasons.append('slippage_high')
        if cost_adjusted_score < thresholds['promotion_score_min']:
            decision = 'reject' if cost_adjusted_score < thresholds['promotion_score_min'] - 0.05 else 'needs_review'
            reasons.append('score_below_threshold')
        if regime_coverage < 0.70:
            decision = 'needs_review' if decision == 'approve' else decision
            reasons.append('regime_coverage_weak')
        row = {
            'evaluation_id': f'prom_{new_cycle_id()}',
            'created_at': utc_now_iso(),
            'model_id': model.get('model_id', 'model_seed'),
            'experiment_id': model.get('experiment_id'),
            'decision': decision,
            'summary_score': summary_score,
            'cost_adjusted_score': cost_adjusted_score,
            'sample_size': sample_size,
            'max_drawdown': max_drawdown,
            'regime_coverage': regime_coverage,
            'slippage_bps': slippage,
            'reasons_json': self.store.to_json(reasons),
            'notes': payload.get('notes', 'phaseh sprint3 promotion policy'),
        }
        self.store.append('promotion_evaluations', row)
        if decision == 'approve':
            self.store.append('model_state_transitions', {
                'transition_id': f'trans_{new_cycle_id()}',
                'created_at': row['created_at'],
                'model_id': row['model_id'],
                'from_state': model.get('state', 'candidate'),
                'to_state': 'approved',
                'reason': 'promotion_policy_approved',
            })
        return self._decode(row)

    def list_latest(self, limit: int = 25) -> list[dict[str, Any]]:
        rows = self.store.fetchall_dict(
            """
            SELECT evaluation_id, created_at, model_id, experiment_id, decision, summary_score,
                   cost_adjusted_score, sample_size, max_drawdown, regime_coverage,
                   slippage_bps, reasons_json, notes
            FROM promotion_evaluations
            ORDER BY created_at DESC
            LIMIT ?
            """,
            [limit],
        )
        return [self._decode(r) for r in rows]

    def ensure_seed(self) -> None:
        count = self.store.fetchone_dict('SELECT COUNT(*) AS c FROM promotion_evaluations')
        if int((count or {}).get('c') or 0) == 0:
            self.evaluate({'notes': 'seed promotion evaluation'})

    def _candidate_model(self, model_id: str | None) -> dict[str, Any]:
        if model_id:
            row = self.store.fetchone_dict(
                'SELECT model_id, experiment_id, model_version, state, validation_metrics_json FROM model_registry WHERE model_id = ? ORDER BY created_at DESC LIMIT 1',
                [model_id],
            )
            if row:
                return row
        row = self.store.fetchone_dict(
            """
            SELECT model_id, experiment_id, model_version, state, validation_metrics_json
            FROM model_registry
            ORDER BY created_at DESC LIMIT 1
            """
        )
        return row or {'model_id': 'model_seed', 'experiment_id': 'exp_seed', 'state': 'candidate', 'validation_metrics_json': '{}'}

    def _validation_for_model(self, model: dict[str, Any]) -> dict[str, Any]:
        row = self.store.fetchone_dict(
            'SELECT summary_score, passed FROM validation_registry WHERE experiment_id = ? ORDER BY created_at DESC LIMIT 1',
            [model.get('experiment_id')],
        )
        return row or {'summary_score': 0.78, 'passed': True}

    def _latest_strategy_metrics(self) -> dict[str, Any]:
        row = self.store.fetchone_dict(
            'SELECT drawdown FROM strategy_performance_daily ORDER BY created_at DESC LIMIT 1'
        )
        return row or {'drawdown': -0.06}

    def _latest_slippage(self) -> float:
        row = self.store.fetchone_dict(
            'SELECT avg_slippage_bps FROM execution_quality_snapshots ORDER BY created_at DESC LIMIT 1'
        )
        return float((row or {}).get('avg_slippage_bps') or 4.5)

    def _metric_from_model(self, model: dict[str, Any], key: str, default: float) -> float:
        metrics = parse_json_field(model.get('validation_metrics_json'), {})
        return float(metrics.get(key, default) or default)

    def _decode(self, row: dict[str, Any]) -> dict[str, Any]:
        out = dict(row)
        out['reasons'] = parse_json_field(out.pop('reasons_json', None), [])
        return out
