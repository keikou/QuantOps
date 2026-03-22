from __future__ import annotations

from ai_hedge_bot.app.container import CONTAINER
from ai_hedge_bot.core.ids import new_cycle_id
from ai_hedge_bot.core.clock import utc_now_iso


def signal_summary() -> dict:
    row = CONTAINER.runtime_store.fetchone_dict(
        """
        SELECT COUNT(*) AS signals_evaluated,
               AVG(CASE WHEN won THEN 1.0 ELSE 0.0 END) AS winrate,
               COUNT(DISTINCT signal_id) AS signal_count
        FROM signal_evaluations
        """
    ) or {'signals_evaluated': 0, 'winrate': None, 'signal_count': 0}
    snapshot = {
        'snapshot_id': new_cycle_id(),
        'created_at': utc_now_iso(),
        'signals_evaluated': int(row['signals_evaluated'] or 0),
        'winrate': None if row['winrate'] is None else round(float(row['winrate']), 4),
        'signal_count': int(row['signal_count'] or 0),
    }
    CONTAINER.runtime_store.append('analytics_signal_summary', snapshot)
    return {'status': 'ok', **{k: v for k, v in snapshot.items() if k not in {'snapshot_id', 'created_at'}}}
