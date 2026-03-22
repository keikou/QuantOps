# Fix: risk_snapshots table auto-create

This runtime bundle fixes the worker crash:

```text
Catalog Error: Table with name risk_snapshots does not exist!
```

## What changed
- `apps/quantops-api/app/repositories/risk_repository.py`
  - added `_ensure_tables(conn)`
  - calls `self._ensure_tables(conn)` before inserting a snapshot

## Result
The worker can persist risk snapshots even when the DuckDB volume starts empty.
