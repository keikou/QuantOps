from __future__ import annotations

from typing import Any

from ai_hedge_bot.app.container import CONTAINER
from ai_hedge_bot.core.clock import utc_now_iso
from ai_hedge_bot.core.ids import new_cycle_id


class StrategyAnalytics:
    def __init__(self) -> None:
        self.store = CONTAINER.runtime_store

    def record_from_allocation(self, bundle: dict[str, Any]) -> None:
        created_at = utc_now_iso()
        latest_fill_rate = float(bundle.get('allocation_totals', {}).get('latest_fill_rate', 0.92))
        latest_slippage_penalty = float(bundle.get('allocation_totals', {}).get('latest_slippage_penalty', 0.02))
        rows = []
        drawdown_rows = []
        for idx, allocation in enumerate(bundle.get('allocations', [])):
            expected_return = round(float(allocation['capital_weight']) * (0.07 - idx * 0.01), 6)
            realized_return = round(expected_return * latest_fill_rate - latest_slippage_penalty * 0.02, 6)
            hit_rate = round(max(0.45, min(0.82, 0.56 + expected_return)), 6)
            turnover = round(0.18 + idx * 0.04, 6)
            drawdown = round(max(0.01, 0.04 + idx * 0.01 - realized_return * 0.2), 6)
            row = {
                'perf_id': new_cycle_id(),
                'created_at': created_at,
                'strategy_id': allocation['strategy_id'],
                'strategy_name': allocation['strategy_name'],
                'capital_weight': float(allocation['capital_weight']),
                'expected_return': expected_return,
                'realized_return': realized_return,
                'hit_rate': hit_rate,
                'turnover': turnover,
                'cost_adjusted_score': round(realized_return - turnover * 0.01, 6),
                'drawdown': drawdown,
            }
            rows.append(row)
            if drawdown >= 0.06:
                drawdown_rows.append(
                    {
                        'event_id': new_cycle_id(),
                        'created_at': created_at,
                        'strategy_id': allocation['strategy_id'],
                        'severity': 'warning' if drawdown < 0.08 else 'critical',
                        'drawdown': drawdown,
                        'notes': 'auto-recorded by PhaseH Sprint1 strategy analytics',
                    }
                )
        if rows:
            self.store.append('strategy_performance_daily', rows)
        if drawdown_rows:
            self.store.append('strategy_drawdown_events', drawdown_rows)

    def summary(self) -> dict[str, Any]:
        strategies = self.store.fetchall_dict(
            """
            SELECT strategy_id, strategy_name, capital_weight, expected_return, realized_return,
                   hit_rate, turnover, cost_adjusted_score, drawdown, created_at
            FROM strategy_performance_daily
            WHERE created_at = (SELECT MAX(created_at) FROM strategy_performance_daily)
            ORDER BY strategy_id
            """
        )
        latest_risk_rows = self.store.fetchall_dict(
            """
            SELECT strategy_id, gross_exposure, net_exposure, capital_weight, risk_budget,
                   budget_usage, concentration_top_symbol, concentration_top_weight, status, created_at
            FROM global_risk_snapshots
            WHERE created_at = (SELECT MAX(created_at) FROM global_risk_snapshots)
            ORDER BY strategy_id
            """
        )
        latest_netting = self.store.fetchall_dict(
            """
            SELECT symbol, gross_before, gross_after, net_exposure, created_at
            FROM cross_strategy_netting_logs
            WHERE created_at = (SELECT MAX(created_at) FROM cross_strategy_netting_logs)
            ORDER BY symbol
            """
        )
        latest_alerts = []
        for row in self.store.fetchall_dict(
            """
            SELECT strategy_id, severity, drawdown, notes
            FROM strategy_drawdown_events
            WHERE created_at = (SELECT MAX(created_at) FROM strategy_drawdown_events)
            ORDER BY strategy_id
            """
        ):
            latest_alerts.append(row)
        aggregate = self.store.fetchone_dict(
            """
            SELECT COUNT(*) AS strategy_count,
                   COALESCE(SUM(capital_weight), 0) AS allocated_capital,
                   COALESCE(AVG(realized_return), 0) AS avg_realized_return,
                   COALESCE(AVG(hit_rate), 0) AS avg_hit_rate,
                   COALESCE(MAX(drawdown), 0) AS max_drawdown
            FROM strategy_performance_daily
            WHERE created_at = (SELECT MAX(created_at) FROM strategy_performance_daily)
            """
        ) or {'strategy_count': 0, 'allocated_capital': 0.0, 'avg_realized_return': 0.0, 'avg_hit_rate': 0.0, 'max_drawdown': 0.0}
        latest_risk_snapshot = {
            'gross_exposure': round(sum(float(r['gross_exposure']) for r in latest_risk_rows), 6) if latest_risk_rows else 0.0,
            'net_exposure': round(sum(float(r['net_exposure']) for r in latest_risk_rows), 6) if latest_risk_rows else 0.0,
            'per_strategy': latest_risk_rows,
            'netting_symbols': latest_netting,
        } if latest_risk_rows else None
        latest_global_risk = {
            'status': 'warning' if any(float(r['budget_usage']) > 1.0 for r in latest_risk_rows) else 'ok',
            'alerts': [row['strategy_id'] for row in latest_alerts],
        }
        return {
            'status': 'ok',
            'aggregate': {
                'strategy_count': int(aggregate['strategy_count'] or 0),
                'allocated_capital': round(float(aggregate['allocated_capital'] or 0.0), 6),
                'avg_realized_return': round(float(aggregate['avg_realized_return'] or 0.0), 6),
                'avg_hit_rate': round(float(aggregate['avg_hit_rate'] or 0.0), 6),
                'max_drawdown': round(float(aggregate['max_drawdown'] or 0.0), 6),
            },
            'strategies': strategies,
            'drawdown_events': latest_alerts,
            'latest_risk_snapshot': latest_risk_snapshot,
            'latest_global_risk': latest_global_risk,
        }


def strategy_summary() -> dict[str, Any]:
    return StrategyAnalytics().summary()
