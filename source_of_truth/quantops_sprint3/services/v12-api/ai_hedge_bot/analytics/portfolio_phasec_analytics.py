from __future__ import annotations

from ai_hedge_bot.analytics.json_safe import dataframe_records_to_json_safe
from ai_hedge_bot.data.storage.duckdb_store import DuckDBStore


def _load_table(store: DuckDBStore, table_name: str, order_by: str = 'timestamp desc') -> list[dict]:
    try:
        df = store.query_df(f'select * from {table_name} order by {order_by}').fillna('')
        return dataframe_records_to_json_safe(df)
    except Exception:
        return []


def load_expected_returns(store: DuckDBStore) -> list[dict]:
    return _load_table(store, 'signal_expected_returns')


def load_portfolio_weights(store: DuckDBStore) -> list[dict]:
    return _load_table(store, 'portfolio_weights')


def load_portfolio_allocations(store: DuckDBStore) -> list[dict]:
    return _load_table(store, 'portfolio_allocations')


def load_portfolio_risk(store: DuckDBStore) -> list[dict]:
    return _load_table(store, 'portfolio_risk_snapshots')


def load_portfolio_summary(store: DuckDBStore) -> dict:
    risk_rows = load_portfolio_risk(store)
    allocation_rows = load_portfolio_allocations(store)
    if not risk_rows:
        return {}
    latest = risk_rows[0]
    portfolio_id = latest.get('portfolio_id')
    related = [row for row in allocation_rows if row.get('portfolio_id') == portfolio_id]
    latest['allocation_count'] = len(related)
    latest['expected_pnl_usd'] = round(sum(float(row.get('expected_pnl_usd', 0.0) or 0.0) for row in related), 4)
    latest['symbols'] = sorted({row.get('symbol') for row in related if row.get('symbol')})
    return latest


def load_paper_pnl(store: DuckDBStore) -> dict:
    try:
        df = store.query_df('select * from fills').fillna('')
    except Exception:
        return {'fill_count': 0, 'gross_notional': 0.0}
    gross_notional = 0.0
    for _, row in df.iterrows():
        try:
            gross_notional += float(row.get('quantity', 0.0) or 0.0) * float(row.get('fill_price', 0.0) or 0.0)
        except Exception:
            continue
    return {'fill_count': int(len(df)), 'gross_notional': round(gross_notional, 4)}
