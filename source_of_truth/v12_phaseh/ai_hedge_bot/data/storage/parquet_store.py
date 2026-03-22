from __future__ import annotations

from pathlib import Path
import json


class ParquetStore:
    """JSON-lines fallback scaffold for PhaseG; replace with real parquet implementation."""
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, record: dict) -> None:
        with self.path.open('a', encoding='utf-8') as f:
            f.write(json.dumps(record, ensure_ascii=False) + '
')
