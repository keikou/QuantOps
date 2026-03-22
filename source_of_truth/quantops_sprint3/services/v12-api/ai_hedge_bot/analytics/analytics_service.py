from __future__ import annotations

import json
from pathlib import Path

from ai_hedge_bot.analytics.signal_analytics import signal_summary
from ai_hedge_bot.analytics.execution_analytics import execution_summary
from ai_hedge_bot.analytics.strategy_analytics import strategy_summary
from ai_hedge_bot.app.container import CONTAINER
from ai_hedge_bot.core.ids import new_cycle_id
from ai_hedge_bot.core.clock import utc_now_iso


class AnalyticsService:
    def __init__(self, runtime_dir: Path | None = None) -> None:
        self.runtime_dir = runtime_dir or Path('runtime')

    def rebuild(self) -> dict:
        return {
            'status': 'ok',
            'action': 'rebuild',
            'signal_rows': (CONTAINER.runtime_store.fetchone_dict('SELECT COUNT(*) AS c FROM signals') or {'c': 0})['c'],
            'portfolio_rows': (CONTAINER.runtime_store.fetchone_dict('SELECT COUNT(*) AS c FROM portfolio_diagnostics') or {'c': 0})['c'],
            'shadow_rows': (CONTAINER.runtime_store.fetchone_dict('SELECT COUNT(*) AS c FROM shadow_orders') or {'c': 0})['c'],
        }

    def signal_summary(self) -> dict:
        return signal_summary()

    def portfolio_summary(self) -> dict:
        row = CONTAINER.runtime_store.fetchone_dict(
            """
            SELECT COUNT(*) AS portfolio_count,
                   COALESCE(SUM(ABS(target_weight)), 0) AS gross_exposure_estimate,
                   COUNT(*) AS latest_weight_count
            FROM portfolio_signal_decisions
            WHERE created_at = (SELECT MAX(created_at) FROM portfolio_signal_decisions)
            """
        ) or {'portfolio_count': 0, 'gross_exposure_estimate': 0.0, 'latest_weight_count': 0}
        latest = CONTAINER.runtime_store.fetchone_dict(
            """
            SELECT input_signals, kept_signals, crowding_flags_json, overlap_penalty_applied
            FROM portfolio_diagnostics
            ORDER BY created_at DESC
            LIMIT 1
            """
        ) or {}
        snapshot = {
            'snapshot_id': new_cycle_id(),
            'created_at': utc_now_iso(),
            'portfolio_count': int(row['portfolio_count'] or 0),
            'gross_exposure_estimate': round(float(row['gross_exposure_estimate'] or 0.0), 6),
            'latest_weight_count': int(row['latest_weight_count'] or 0),
        }
        CONTAINER.runtime_store.append('analytics_portfolio_summary', snapshot)
        if latest.get('crowding_flags_json'):
            latest['crowding_flags'] = json.loads(latest.pop('crowding_flags_json'))
        return {'status': 'ok', 'portfolio_count': snapshot['portfolio_count'], 'latest': latest, 'gross_exposure_estimate': snapshot['gross_exposure_estimate'], 'latest_weight_count': snapshot['latest_weight_count']}

    def shadow_summary(self) -> dict:
        counts = CONTAINER.runtime_store.fetchone_dict(
            """
            SELECT COUNT(DISTINCT cycle_id) AS shadow_cycles,
                   COUNT(*) AS shadow_order_count
            FROM shadow_orders
            """
        ) or {'shadow_cycles': 0, 'shadow_order_count': 0}
        fill_count = CONTAINER.runtime_store.fetchone_dict('SELECT COUNT(*) AS c FROM shadow_fills') or {'c': 0}
        latest_pnl = CONTAINER.runtime_store.fetchone_dict(
            'SELECT * EXCLUDE(snapshot_id, run_id, cycle_id) FROM shadow_pnl_snapshots ORDER BY created_at DESC LIMIT 1'
        ) or {}
        snapshot = {
            'snapshot_id': new_cycle_id(),
            'created_at': utc_now_iso(),
            'shadow_cycles': int(counts['shadow_cycles'] or 0),
            'shadow_order_count': int(counts['shadow_order_count'] or 0),
            'shadow_fill_count': int(fill_count['c'] or 0),
            'latest_pnl_json': CONTAINER.runtime_store.to_json(latest_pnl),
        }
        CONTAINER.runtime_store.append('analytics_shadow_summary', snapshot)
        return {
            'status': 'ok',
            'shadow_cycles': snapshot['shadow_cycles'],
            'shadow_order_count': snapshot['shadow_order_count'],
            'shadow_fill_count': snapshot['shadow_fill_count'],
            'latest_pnl': latest_pnl,
        }

    def execution_quality(self) -> dict:
        return execution_summary()

    def strategy_summary(self) -> dict:
        return strategy_summary()

    def mode_comparison(self) -> dict:
        paper = CONTAINER.runtime_store.fetchone_dict("SELECT COUNT(*) AS c FROM orchestrator_cycles WHERE mode='paper'") or {'c': 0}
        shadow = CONTAINER.runtime_store.fetchone_dict("SELECT COUNT(*) AS c FROM orchestrator_cycles WHERE mode='shadow'") or {'c': 0}
        return {'status': 'ok', 'paper_cycles': int(paper['c'] or 0), 'shadow_cycles': int(shadow['c'] or 0)}
