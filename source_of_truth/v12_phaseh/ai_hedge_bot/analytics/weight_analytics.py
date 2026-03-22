from __future__ import annotations

from ai_hedge_bot.analytics.json_safe import dataframe_records_to_json_safe
from ai_hedge_bot.data.storage.duckdb_store import DuckDBStore


def load_weight_history(store: DuckDBStore) -> list[dict]:
    try:
        df = store.query_df('select * from weight_updates').fillna('')
        return dataframe_records_to_json_safe(df)
    except Exception:
        return []
