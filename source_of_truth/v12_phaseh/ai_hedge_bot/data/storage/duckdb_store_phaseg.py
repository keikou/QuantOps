from __future__ import annotations

from pathlib import Path
import duckdb


class PhaseGDuckDBStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def execute(self, sql: str):
        with duckdb.connect(str(self.path)) as conn:
            return conn.execute(sql).fetchall()
