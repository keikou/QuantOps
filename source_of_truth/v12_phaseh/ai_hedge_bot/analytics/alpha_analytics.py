from __future__ import annotations

from ai_hedge_bot.analytics.json_safe import dataframe_records_to_json_safe
from ai_hedge_bot.data.storage.duckdb_store import DuckDBStore


def load_alpha_performance(store: DuckDBStore) -> list[dict]:
    try:
        df = store.query_df('select * from alpha_performance_summary').fillna('')
        return dataframe_records_to_json_safe(df)
    except Exception:
        return []
