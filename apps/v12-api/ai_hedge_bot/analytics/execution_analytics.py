from __future__ import annotations

from ai_hedge_bot.app.container import CONTAINER
from ai_hedge_bot.core.ids import new_cycle_id
from ai_hedge_bot.core.clock import utc_now_iso


def execution_summary() -> dict:
    row = CONTAINER.runtime_store.fetchone_dict(
        """
        SELECT AVG(avg_slippage_bps) AS avg_slippage_bps,
               AVG(fill_rate) AS fill_rate,
               SUM(order_count) AS order_count,
               SUM(fill_count) AS fill_count
        FROM execution_quality_snapshots
        WHERE mode = 'shadow'
        """
    ) or {'avg_slippage_bps': None, 'fill_rate': None, 'order_count': 0, 'fill_count': 0}
    snapshot = {
        'snapshot_id': new_cycle_id(),
        'created_at': utc_now_iso(),
        'avg_slippage_bps': None if row['avg_slippage_bps'] is None else round(float(row['avg_slippage_bps']), 4),
        'fill_rate': None if row['fill_rate'] is None else round(float(row['fill_rate']), 4),
        'order_count': int(row['order_count'] or 0),
        'fill_count': int(row['fill_count'] or 0),
    }
    CONTAINER.runtime_store.append('analytics_execution_summary', snapshot)
    return {'status': 'ok', **{k: v for k, v in snapshot.items() if k not in {'snapshot_id', 'created_at'}}}
