from __future__ import annotations

from typing import Any

from ai_hedge_bot.app.container import CONTAINER
from ai_hedge_bot.core.clock import utc_now_iso
from ai_hedge_bot.core.ids import new_cycle_id


class RiskBudgetEngine:
    def __init__(self) -> None:
        self.store = CONTAINER.runtime_store

    def build(self, allocations: list[dict[str, Any]], netting: dict[str, Any]) -> dict[str, Any]:
        created_at = utc_now_iso()
        gross_after = float(netting.get('gross_after', 0.0))
        symbol_exposures = netting.get('symbol_exposures', {})
        top_symbol = None
        top_symbol_weight = 0.0
        if symbol_exposures:
            top_symbol, top_symbol_weight = max(symbol_exposures.items(), key=lambda kv: abs(float(kv[1])))
            top_symbol_weight = abs(float(top_symbol_weight))

        per_strategy = []
        rows = []
        for allocation in allocations:
            strategy_id = allocation['strategy_id']
            capital_weight = float(allocation['capital_weight'])
            risk_budget = float(allocation['risk_budget'])
            usage = round(capital_weight / max(risk_budget, 1e-9), 6)
            status = 'ok' if usage <= 1.0 else 'breach'
            item = {
                'strategy_id': strategy_id,
                'capital_weight': round(capital_weight, 6),
                'risk_budget': round(risk_budget, 6),
                'budget_usage': usage,
                'status': status,
            }
            per_strategy.append(item)
            rows.append(
                {
                    'snapshot_id': new_cycle_id(),
                    'created_at': created_at,
                    'strategy_id': strategy_id,
                    'gross_exposure': round(gross_after, 6),
                    'net_exposure': round(sum(float(v) for v in symbol_exposures.values()), 6),
                    'capital_weight': item['capital_weight'],
                    'risk_budget': item['risk_budget'],
                    'budget_usage': usage,
                    'concentration_top_symbol': top_symbol,
                    'concentration_top_weight': round(top_symbol_weight, 6),
                    'status': status,
                }
            )
        if rows:
            self.store.append('global_risk_snapshots', rows)
        return {
            'status': 'ok',
            'generated_at': created_at,
            'gross_exposure': round(gross_after, 6),
            'net_exposure': round(sum(float(v) for v in symbol_exposures.values()), 6),
            'concentration_top_symbol': top_symbol,
            'concentration_top_weight': round(top_symbol_weight, 6),
            'per_strategy': per_strategy,
        }
