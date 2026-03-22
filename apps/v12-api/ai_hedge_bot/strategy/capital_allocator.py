from __future__ import annotations

from collections import defaultdict
from typing import Any

from ai_hedge_bot.app.container import CONTAINER
from ai_hedge_bot.core.clock import utc_now_iso
from ai_hedge_bot.core.ids import new_cycle_id
from ai_hedge_bot.strategy.strategy_registry import StrategyRegistry


class CapitalAllocator:
    def __init__(self) -> None:
        self.store = CONTAINER.runtime_store
        self.registry = StrategyRegistry()

    def allocate(self) -> dict[str, Any]:
        latest_signals = self.store.fetchall_dict(
            """
            SELECT signal_id, symbol, side, score, alpha_family, dominant_alpha, horizon, turnover_profile, regime
            FROM signals
            WHERE created_at = (SELECT MAX(created_at) FROM signals)
            ORDER BY symbol
            """
        )
        if not latest_signals:
            latest_signals = []
        runtimes = self.registry.runtimes()
        targets_by_strategy: dict[str, list[dict[str, Any]]] = {}
        raw_scores: dict[str, float] = {}
        latest_fill_rate = self._latest_fill_rate()
        latest_slippage_penalty = self._latest_slippage_penalty()
        created_at = utc_now_iso()

        runtime_rows: list[dict[str, Any]] = []
        alloc_rows: list[dict[str, Any]] = []
        total_raw = 0.0
        for runtime in runtimes:
            runtime.initialize()
            runtime.on_market_data({'market_ts': created_at})
            targets = runtime.build_target(latest_signals)
            state = runtime.state.to_dict()
            runtime_rows.append({'strategy_id': runtime.strategy_id, **state})
            targets_by_strategy[runtime.strategy_id] = targets
            signal_strength = sum(abs(float(t.get('score', 0.0))) for t in targets)
            priority_boost = max(0.25, 1.0 - (self._priority(runtime.strategy_id) - 1) * 0.15)
            quality_boost = max(0.35, latest_fill_rate - latest_slippage_penalty)
            raw = max(signal_strength, 0.05) * priority_boost * quality_boost
            raw_scores[runtime.strategy_id] = raw
            total_raw += raw

        self.store.append('strategy_runtime_state', runtime_rows)

        if total_raw <= 0:
            total_raw = float(len(runtimes) or 1)
            raw_scores = {r.strategy_id: 1.0 for r in runtimes}

        allocations: list[dict[str, Any]] = []
        for row in self.registry.active():
            strategy_id = row['strategy_id']
            normalized = float(raw_scores.get(strategy_id, 0.0)) / total_raw
            proposed = min(normalized, float(row['capital_cap']))
            score = round(normalized * 100.0, 6)
            allocation = {
                'allocation_id': new_cycle_id(),
                'created_at': created_at,
                'strategy_id': strategy_id,
                'strategy_name': row['name'],
                'capital_weight': round(proposed, 6),
                'capital_cap': round(float(row['capital_cap']), 6),
                'risk_budget': round(float(row['risk_budget']), 6),
                'score': score,
                'signal_count': len(targets_by_strategy.get(strategy_id, [])),
                'active_symbols': sorted({t['symbol'] for t in targets_by_strategy.get(strategy_id, [])}),
            }
            allocations.append(allocation)
            alloc_rows.append(
                {
                    'allocation_id': allocation['allocation_id'],
                    'created_at': created_at,
                    'strategy_id': strategy_id,
                    'capital_weight': allocation['capital_weight'],
                    'capital_cap': allocation['capital_cap'],
                    'risk_budget': allocation['risk_budget'],
                    'score': allocation['score'],
                    'signal_count': allocation['signal_count'],
                    'active_symbols_json': self.store.to_json(allocation['active_symbols']),
                }
            )

        total_allocated = sum(a['capital_weight'] for a in allocations)
        if total_allocated > 0:
            scale = min(1.0, 1.0 / total_allocated)
            for allocation in allocations:
                allocation['capital_weight'] = round(allocation['capital_weight'] * scale, 6)
            for row in alloc_rows:
                row['capital_weight'] = round(float(row['capital_weight']) * scale, 6)

        self.store.append('global_capital_allocations', alloc_rows)
        return {
            'status': 'ok',
            'generated_at': created_at,
            'allocations': allocations,
            'totals': {
                'strategy_count': len(allocations),
                'capital_allocated': round(sum(a['capital_weight'] for a in allocations), 6),
                'latest_fill_rate': latest_fill_rate,
                'latest_slippage_penalty': latest_slippage_penalty,
            },
            'targets_by_strategy': targets_by_strategy,
        }

    def _priority(self, strategy_id: str) -> int:
        row = self.store.fetchone_dict('SELECT priority FROM strategy_registry WHERE strategy_id = ?', [strategy_id]) or {'priority': 3}
        return int(row['priority'] or 3)

    def _latest_fill_rate(self) -> float:
        row = self.store.fetchone_dict('SELECT fill_rate FROM execution_quality_snapshots ORDER BY created_at DESC LIMIT 1') or {'fill_rate': 0.92}
        return round(float(row['fill_rate'] or 0.92), 6)

    def _latest_slippage_penalty(self) -> float:
        row = self.store.fetchone_dict('SELECT avg_slippage_bps FROM execution_quality_snapshots ORDER BY created_at DESC LIMIT 1') or {'avg_slippage_bps': 2.5}
        return round(min(float(row['avg_slippage_bps'] or 0.0) / 100.0, 0.35), 6)
