from __future__ import annotations

from pathlib import Path
import sqlite3
import re

from app.core.config import get_settings
from app.repositories.duckdb import DuckDBConnectionFactory


BASE_DIR = Path(__file__).parent
MIGRATIONS_DIR = BASE_DIR / "migrations"
SEED_DIR = BASE_DIR / "seed"


def _is_sqlite_connection(conn) -> bool:
    return isinstance(conn, sqlite3.Connection)


def _sqlite_column_exists(conn, table_name: str, column_name: str) -> bool:
    rows = conn.execute(f"PRAGMA table_info('{table_name}')").fetchall()
    return any((row[1] if len(row) > 1 else None) == column_name for row in rows)


def _normalize_sqlite_sql(sql: str) -> str:
    normalized = sql.replace('NOW()', 'CURRENT_TIMESTAMP')
    normalized = re.sub(r'\bTRUE\b', '1', normalized, flags=re.IGNORECASE)
    normalized = re.sub(r'\bFALSE\b', '0', normalized, flags=re.IGNORECASE)
    return normalized


def _execute_sql(conn, sql: str) -> None:
    sql = sql.strip()
    if not sql:
        return
    if _is_sqlite_connection(conn):
        normalized = _normalize_sqlite_sql(sql)
        statements = [stmt.strip() for stmt in normalized.split(';') if stmt.strip()]
        for stmt in statements:
            match = re.match(r"ALTER TABLE\s+(?P<table>\w+)\s+ADD COLUMN\s+IF NOT EXISTS\s+(?P<column>\w+)\s+(?P<type>.+)", stmt, flags=re.IGNORECASE | re.DOTALL)
            if match:
                table_name = match.group('table')
                column_name = match.group('column')
                column_type = match.group('type').strip()
                if not _sqlite_column_exists(conn, table_name, column_name):
                    conn.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}")
            else:
                conn.execute(stmt)
        return
    conn.execute(sql)


def run_migrations(db_path: str | Path, migrations_dir: Path = MIGRATIONS_DIR, seed_dir: Path = SEED_DIR) -> None:
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    factory = DuckDBConnectionFactory(str(db_path))
    with factory.connect() as conn:
        _execute_sql(conn, "CREATE TABLE IF NOT EXISTS schema_migrations(version TEXT PRIMARY KEY, applied_at TIMESTAMP DEFAULT NOW())")
        applied = {row[0] for row in conn.execute("SELECT version FROM schema_migrations").fetchall()}

        for file in sorted(migrations_dir.glob("*.sql")):
            if file.name in applied:
                continue
            sql = file.read_text(encoding="utf-8").strip()
            if not sql:
                continue
            _execute_sql(conn, sql)
            conn.execute("INSERT INTO schema_migrations(version) VALUES (?)", [file.name])

        scheduler_seed = seed_dir / "scheduler_jobs.sql"
        if scheduler_seed.exists():
            seed_sql = scheduler_seed.read_text(encoding="utf-8").strip()
            if seed_sql:
                _execute_sql(conn, seed_sql)

        conn.commit()


def main() -> None:
    settings = get_settings()
    run_migrations(settings.db_path)
    print(f"migrations applied to {settings.db_path}")


if __name__ == "__main__":
    main()
