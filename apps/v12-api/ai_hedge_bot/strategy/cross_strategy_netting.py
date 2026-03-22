from __future__ import annotations

from collections import defaultdict
from typing import Any

from ai_hedge_bot.app.container import CONTAINER
from ai_hedge_bot.core.clock import utc_now_iso
from ai_hedge_bot.core.ids import new_cycle_id


class CrossStrategyNetting:
    def __init__(self) -> None:
        self.store = CONTAINER.runtime_store

    def evaluate(self, allocations: list[dict[str, Any]], targets_by_strategy: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
        created_at = utc_now_iso()
        alloc_map = {a['strategy_id']: float(a['capital_weight']) for a in allocations}
        symbol_gross = defaultdict(float)
        symbol_net = defaultdict(float)
        contributions: list[dict[str, Any]] = []
        for strategy_id, targets in targets_by_strategy.items():
            total_hint = sum(abs(float(t.get('target_weight_hint', 0.0))) for t in targets) or 1.0
            for target in targets:
                symbol = target['symbol']
                side = target['side']
                signed = (1.0 if side == 'long' else -1.0) * alloc_map.get(strategy_id, 0.0) * abs(float(target.get('target_weight_hint', 0.0))) / total_hint
                symbol_gross[symbol] += abs(signed)
                symbol_net[symbol] += signed
                contributions.append(
                    {
                        'strategy_id': strategy_id,
                        'symbol': symbol,
                        'signed_weight': round(signed, 6),
                    }
                )

        gross_before = round(sum(symbol_gross.values()), 6)
        gross_after = round(sum(abs(v) for v in symbol_net.values()), 6)
        netting_benefit = round(max(gross_before - gross_after, 0.0), 6)
        efficiency = round(netting_benefit / gross_before, 6) if gross_before else 0.0
        rows = []
        for symbol in sorted(set(symbol_net.keys()) | set(symbol_gross.keys())):
            rows.append(
                {
                    'netting_log_id': new_cycle_id(),
                    'created_at': created_at,
                    'symbol': symbol,
                    'gross_before': round(symbol_gross.get(symbol, 0.0), 6),
                    'gross_after': round(abs(symbol_net.get(symbol, 0.0)), 6),
                    'net_exposure': round(symbol_net.get(symbol, 0.0), 6),
                    'contributions_json': self.store.to_json([c for c in contributions if c['symbol'] == symbol]),
                }
            )
        if rows:
            self.store.append('cross_strategy_netting_logs', rows)
        return {
            'status': 'ok',
            'generated_at': created_at,
            'gross_before': gross_before,
            'gross_after': gross_after,
            'netting_benefit': netting_benefit,
            'netting_efficiency': efficiency,
            'symbol_exposures': {k: round(v, 6) for k, v in sorted(symbol_net.items())},
        }
