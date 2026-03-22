from __future__ import annotations

import json
import sys
from pathlib import Path

import duckdb

TARGET_TABLES = [
    'signals',
    'signal_evaluations',
    'portfolio_signal_decisions',
    'portfolio_diagnostics',
    'orchestrator_runs',
    'orchestrator_cycles',
    'execution_quality_snapshots',
    'analytics_signal_summary',
    'analytics_portfolio_summary',
    'analytics_execution_summary',
    'analytics_shadow_summary',
]

PREVIEW_TABLES = [
    'signals',
    'portfolio_signal_decisions',
    'orchestrator_runs',
    'orchestrator_cycles',
    'execution_quality_snapshots',
]


def choose_db() -> Path | None:
    if len(sys.argv) > 1:
        p = Path(sys.argv[1])
        if p.exists():
            return p
    runtime_db = Path('runtime/analytics.duckdb')
    if runtime_db.exists():
        return runtime_db
    cands = list(Path('.').rglob('*.duckdb')) + list(Path('.').rglob('*.db'))
    return cands[0] if cands else None


def fetchall_dict(conn: duckdb.DuckDBPyConnection, sql: str):
    cur = conn.execute(sql)
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, row)) for row in cur.fetchall()]


def main() -> int:
    db = choose_db()
    if db is None:
        print('ERROR: no DuckDB file found')
        return 2
    print(f'[INFO] Using DB: {db}')
    conn = duckdb.connect(str(db), read_only=True)
    tables = {r[0] for r in conn.execute('SHOW TABLES').fetchall()}
    counts = {}
    print('\n=== TABLE COUNTS ===')
    for table in TARGET_TABLES:
        if table not in tables:
            print(f'{table}: MISSING')
            continue
        count = conn.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0]
        counts[table] = int(count)
        print(f'{table}: {count}')
    print('\n=== PREVIEW ROWS ===')
    for table in PREVIEW_TABLES:
        print(f'\n[{table}]')
        if table not in tables:
            print('MISSING')
            continue
        rows = fetchall_dict(conn, f'SELECT * FROM {table} ORDER BY 2 DESC LIMIT 3')
        print(json.dumps(rows, ensure_ascii=False, indent=2, default=str))
    problems = []
    if counts.get('signals', 0) == 0:
        problems.append('signals table has 0 rows')
    if counts.get('portfolio_signal_decisions', 0) == 0:
        problems.append('portfolio_signal_decisions table has 0 rows')
    if counts.get('orchestrator_runs', 0) == 0 or counts.get('orchestrator_cycles', 0) == 0:
        problems.append('orchestrator tables have 0 rows')
    if counts.get('execution_quality_snapshots', 0) == 0:
        problems.append('execution_quality_snapshots table has 0 rows')
    if counts.get('analytics_signal_summary', 0) == 0:
        problems.append('analytics_signal_summary table has 0 rows')
    if counts.get('analytics_execution_summary', 0) == 0:
        problems.append('analytics_execution_summary table has 0 rows')
    print('\n=== DIAGNOSIS ===')
    if problems:
        for p in problems:
            print(f'- {p}')
        return 1
    print('OK: core runtime -> analytics tables are populated.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
