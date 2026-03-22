from __future__ import annotations

from pathlib import Path

import duckdb

from app.core.config import get_settings


BASE_DIR = Path(__file__).parent
MIGRATIONS_DIR = BASE_DIR / "migrations"
SEED_DIR = BASE_DIR / "seed"


def main() -> None:
    settings = get_settings()
    db_path = Path(settings.db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = duckdb.connect(str(db_path))
    conn.execute("CREATE TABLE IF NOT EXISTS schema_migrations(version TEXT PRIMARY KEY, applied_at TIMESTAMP DEFAULT NOW())")
    applied = {row[0] for row in conn.execute("SELECT version FROM schema_migrations").fetchall()}
    for file in sorted(MIGRATIONS_DIR.glob("*.sql")):
        if file.name in applied:
            continue
        conn.execute(file.read_text(encoding="utf-8"))
        conn.execute("INSERT INTO schema_migrations(version) VALUES (?)", [file.name])
    scheduler_seed = SEED_DIR / "scheduler_jobs.sql"
    if scheduler_seed.exists():
        conn.execute(scheduler_seed.read_text(encoding="utf-8"))
    conn.close()
    print(f"migrations applied to {db_path}")


if __name__ == "__main__":
    main()
