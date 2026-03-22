# Sprint4 FINAL v7 fix

This build fixes QuantOps worker startup by initializing DuckDB with an explicit path.

## Fixed file
- `apps/quantops-api/app/db/init_db.py`

## Change
Replaced:
```python
factory = DuckDBConnectionFactory()
```

With:
```python
db_path = os.getenv("QUANTOPS_DB_PATH", "/app/data/quantops.duckdb")
factory = DuckDBConnectionFactory(db_path)
```

## Effect
- Worker bootstrap no longer fails with:
  `TypeError: DuckDBConnectionFactory.__init__() missing 1 required positional argument: 'db_path'`
- Uses the same DB path configured in docker-compose.
