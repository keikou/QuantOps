from __future__ import annotations

from typing import Any


class GlobalRiskEngine:
    def assess(self, risk_snapshot: dict[str, Any]) -> dict[str, Any]:
        gross_exposure = float(risk_snapshot.get('gross_exposure', 0.0))
        top_weight = float(risk_snapshot.get('concentration_top_weight', 0.0))
        alerts: list[str] = []
        if gross_exposure > 1.05:
            alerts.append('gross_exposure_above_soft_limit')
        if top_weight > 0.45:
            alerts.append('symbol_concentration_high')
        breached = [row['strategy_id'] for row in risk_snapshot.get('per_strategy', []) if row.get('status') == 'breach']
        if breached:
            alerts.append('strategy_budget_breach')
        return {
            'status': 'ok' if not alerts else 'warning',
            'alerts': alerts,
            'breached_strategies': breached,
            'gross_exposure': gross_exposure,
            'concentration_top_weight': top_weight,
        }
