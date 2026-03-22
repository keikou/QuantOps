from __future__ import annotations

from pathlib import Path
import json
import pandas as pd

try:
    import duckdb  # type: ignore
except Exception:  # pragma: no cover
    duckdb = None


class DuckDBStore:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._frames: dict[str, pd.DataFrame] = {}

    def sync_jsonl(self, table_name: str, jsonl_path: Path) -> int:
        if not jsonl_path.exists():
            return 0
        rows = [json.loads(line) for line in jsonl_path.read_text(encoding='utf-8').splitlines() if line.strip()]
        if not rows:
            return 0
        df = pd.json_normalize(rows)
        self._frames[table_name] = df
        if duckdb is not None:
            con = duckdb.connect(str(self.db_path))
            con.register('df_view', df)
            con.execute(f"CREATE OR REPLACE TABLE {table_name} AS SELECT * FROM df_view")
            con.close()
        return len(df)

    def query_df(self, sql: str) -> pd.DataFrame:
        if duckdb is not None and self.db_path.exists():
            con = duckdb.connect(str(self.db_path))
            try:
                return con.execute(sql).df()
            finally:
                con.close()
        sql_norm = sql.strip().lower()
        for table, df in self._frames.items():
            if f'from {table.lower()}' in sql_norm:
                return df.copy()
        raise ValueError('No matching in-memory table')
