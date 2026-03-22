from __future__ import annotations

from datetime import datetime, timezone

from ai_hedge_bot.data.storage.duckdb_store import DuckDBStore


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def run(store: DuckDBStore) -> dict[str, int]:
    counts: dict[str, int] = {}
    try:
        fills = store.query_df('select * from shadow_fills')
        costs = store.query_df('select * from execution_costs')
        latency = store.query_df('select * from latency_snapshots')
        pnl = store.query_df('select * from shadow_pnl_snapshots')
    except Exception:
        return {'execution_quality_snapshots': 0, 'slippage_reports': 0, 'latency_snapshots': 0, 'shadow_pnl_snapshots': 0}

    if not fills.empty:
        eq = fills.groupby(['symbol', 'maker_taker'], dropna=False).agg(fill_count=('fill_id', 'count'), avg_fee_bps=('fee_bps', 'mean')).reset_index()
        eq['timestamp'] = _utc_now_iso()
        store._frames['execution_quality_snapshots'] = eq
        counts['execution_quality_snapshots'] = len(eq)
        if hasattr(store, 'sync_jsonl'):
            pass
    else:
        counts['execution_quality_snapshots'] = 0
    if not costs.empty:
        sr = costs.groupby('symbol', dropna=False).agg(avg_slippage_bps=('slippage_bps', 'mean'), avg_total_cost_bps=('total_cost_bps', 'mean')).reset_index()
        sr['timestamp'] = _utc_now_iso()
        store._frames['slippage_reports'] = sr
        counts['slippage_reports'] = len(sr)
    else:
        counts['slippage_reports'] = 0
    counts['latency_snapshots'] = len(latency)
    counts['shadow_pnl_snapshots'] = len(pnl)
    # persist snapshot frames into duckdb if available
    for table in ('execution_quality_snapshots','slippage_reports'):
        if table in store._frames:
            df = store._frames[table]
            try:
                import duckdb  # type: ignore
                con = duckdb.connect(str(store.db_path))
                con.register('df_view', df)
                con.execute(f'CREATE OR REPLACE TABLE {table} AS SELECT * FROM df_view')
                con.close()
            except Exception:
                pass
    return counts
