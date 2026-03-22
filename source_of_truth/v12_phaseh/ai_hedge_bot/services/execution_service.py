from __future__ import annotations

from ai_hedge_bot.analytics.json_safe import dataframe_records_to_json_safe
from ai_hedge_bot.data.storage.duckdb_store import DuckDBStore


def _query(store: DuckDBStore, sql: str) -> list[dict]:
    try:
        df = store.query_df(sql).fillna('')
        return dataframe_records_to_json_safe(df)
    except Exception:
        return []


class ExecutionAnalyticsService:
    def __init__(self, store: DuckDBStore) -> None:
        self.store = store

    def shadow_orders(self) -> list[dict]:
        return _query(self.store, 'select * from shadow_orders order by created_ts desc')

    def shadow_fills(self) -> list[dict]:
        return _query(self.store, 'select * from shadow_fills order by fill_ts desc')

    def execution_quality(self) -> list[dict]:
        rows = _query(self.store, 'select * from execution_quality_snapshots order by timestamp desc')
        if rows:
            return rows
        try:
            fills = self.store.query_df('select * from shadow_fills')
            if fills.empty:
                return []
            agg = fills.groupby('symbol', dropna=False).agg(fill_count=('fill_id','count'), avg_fee_bps=('fee_bps','mean')).reset_index()
            agg['timestamp'] = ''
            return dataframe_records_to_json_safe(agg)
        except Exception:
            return []

    def shadow_summary(self) -> dict:
        try:
            fills = self.store.query_df('select * from shadow_fills')
            costs = self.store.query_df('select * from execution_costs')
            pnl = self.store.query_df('select * from shadow_pnl_snapshots')
        except Exception:
            return {'orders_count': 0, 'fills_count': 0, 'fill_ratio': 0.0}
        orders_count = 0
        try:
            orders_count = len(self.store.query_df('select * from shadow_orders'))
        except Exception:
            pass
        fills_count = int(len(fills))
        fill_ratio = round(fills_count / orders_count, 6) if orders_count else 0.0
        avg_slippage = round(float(costs['slippage_bps'].mean()), 6) if not costs.empty else 0.0
        avg_latency = 0.0
        try:
            latency = self.store.query_df('select * from latency_snapshots')
            if not latency.empty:
                avg_latency = round(float(latency['order_to_complete_ms'].mean()), 6)
        except Exception:
            pass
        total_fee = round(float(fills['fee_usd'].sum()), 6) if not fills.empty else 0.0
        shadow_realized = round(float(pnl['net_shadow_pnl_usd'].sum()), 6) if not pnl.empty else 0.0
        execution_drag = round(float(pnl['execution_drag_usd'].sum()), 6) if not pnl.empty else 0.0
        return {'orders_count': orders_count, 'fills_count': fills_count, 'fill_ratio': fill_ratio, 'avg_signed_slippage_bps': avg_slippage, 'avg_latency_ms': avg_latency, 'total_fee_usd': total_fee, 'shadow_realized_pnl_usd': shadow_realized, 'execution_drag_usd': execution_drag}

    def slippage_report(self) -> list[dict]:
        return _query(self.store, 'select * from slippage_reports order by timestamp desc')

    def order_lifecycle(self) -> list[dict]:
        return _query(self.store, 'select * from order_state_transitions order by transition_ts desc')

    def latency(self) -> list[dict]:
        return _query(self.store, 'select * from latency_snapshots order by timestamp desc')
