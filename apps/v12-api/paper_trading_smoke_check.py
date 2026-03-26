### Sample of how to test
#python paper_trading_smoke_check.py --db ./runtime/runtime.duckdb --show-samples
#
from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from typing import Any

import duckdb


@dataclass
class CheckResult:
    name: str
    status: str   # PASS / WARN / FAIL
    message: str


def q1(conn: duckdb.DuckDBPyConnection, sql: str, params: list[Any] | None = None) -> Any:
    return conn.execute(sql, params or []).fetchone()


def qall(conn: duckdb.DuckDBPyConnection, sql: str, params: list[Any] | None = None) -> list[tuple]:
    return conn.execute(sql, params or []).fetchall()


def table_exists(conn: duckdb.DuckDBPyConnection, table_name: str) -> bool:
    row = q1(
        conn,
        """
        SELECT COUNT(*)
        FROM information_schema.tables
        WHERE table_name = ?
        """,
        [table_name],
    )
    return bool(row and row[0] > 0)


def column_exists(conn: duckdb.DuckDBPyConnection, table_name: str, column_name: str) -> bool:
    row = q1(
        conn,
        """
        SELECT COUNT(*)
        FROM information_schema.columns
        WHERE table_name = ? AND column_name = ?
        """,
        [table_name, column_name],
    )
    return bool(row and row[0] > 0)


def safe_count(conn: duckdb.DuckDBPyConnection, table_name: str) -> int | None:
    if not table_exists(conn, table_name):
        return None
    row = q1(conn, f"SELECT COUNT(*) FROM {table_name}")
    return int(row[0]) if row else 0


def latest_rows(
    conn: duckdb.DuckDBPyConnection,
    table_name: str,
    order_col: str,
    limit: int = 5,
) -> list[tuple]:
    if not table_exists(conn, table_name):
        return []
    try:
        return qall(conn, f"SELECT * FROM {table_name} ORDER BY {order_col} DESC LIMIT {limit}")
    except Exception:
        return []


def check_required_tables(conn: duckdb.DuckDBPyConnection) -> list[CheckResult]:
    tables = [
        "cash_ledger",
        "execution_orders",
        "execution_fills",
        "position_snapshots_latest",
        "equity_snapshots",
        "market_prices_latest",
        "position_snapshot_versions",
        "execution_state_snapshots",
        "execution_block_reasons",
    ]
    out: list[CheckResult] = []
    for t in tables:
        exists = table_exists(conn, t)
        out.append(
            CheckResult(
                name=f"table:{t}",
                status="PASS" if exists else "FAIL",
                message="exists" if exists else "missing",
            )
        )
    return out


def check_cash_ledger(conn: duckdb.DuckDBPyConnection) -> CheckResult:
    table = "cash_ledger"
    if not table_exists(conn, table):
        return CheckResult("cash_ledger", "FAIL", "table missing")

    total = safe_count(conn, table) or 0

    has_initial_capital = False
    if column_exists(conn, table, "event_type"):
        row = q1(conn, "SELECT COUNT(*) FROM cash_ledger WHERE event_type = 'initial_capital'")
        has_initial_capital = bool(row and row[0] > 0)

    if total == 0:
        return CheckResult("cash_ledger", "WARN", "empty table")
    if not has_initial_capital:
        return CheckResult("cash_ledger", "WARN", f"{total} rows, but no initial_capital row found")
    return CheckResult("cash_ledger", "PASS", f"{total} rows, initial_capital present")


def check_execution_orders(conn: duckdb.DuckDBPyConnection) -> CheckResult:
    table = "execution_orders"
    if not table_exists(conn, table):
        return CheckResult(table, "FAIL", "table missing")

    total = safe_count(conn, table) or 0
    if total == 0:
        return CheckResult(table, "WARN", "no orders yet")

    parts: list[str] = [f"{total} rows"]

    if column_exists(conn, table, "status"):
        rows = qall(
            conn,
            """
            SELECT status, COUNT(*)
            FROM execution_orders
            GROUP BY status
            ORDER BY COUNT(*) DESC
            """
        )
        status_summary = ", ".join(f"{status}={cnt}" for status, cnt in rows)
        parts.append(f"statuses: {status_summary}")

    return CheckResult(table, "PASS", " | ".join(parts))


def check_execution_fills(conn: duckdb.DuckDBPyConnection) -> CheckResult:
    table = "execution_fills"
    if not table_exists(conn, table):
        return CheckResult(table, "FAIL", "table missing")

    total = safe_count(conn, table) or 0
    if total == 0:
        return CheckResult(table, "WARN", "no fills yet")

    qty_col = "fill_qty" if column_exists(conn, table, "fill_qty") else ("qty" if column_exists(conn, table, "qty") else None)

    if qty_col:
        row = q1(conn, f"SELECT COALESCE(SUM({qty_col}), 0) FROM execution_fills")
        total_qty = float(row[0] or 0.0)
        return CheckResult(table, "PASS", f"{total} rows | total_{qty_col}={total_qty:.6f}")

    return CheckResult(table, "WARN", f"{total} rows, but neither fill_qty nor qty column found")


def check_position_snapshots_latest(conn: duckdb.DuckDBPyConnection) -> CheckResult:
    table = "position_snapshots_latest"
    if not table_exists(conn, table):
        return CheckResult(table, "FAIL", "table missing")

    total = safe_count(conn, table) or 0
    if total == 0:
        return CheckResult(table, "WARN", "no active positions")

    parts: list[str] = [f"{total} rows"]
    if column_exists(conn, table, "signed_qty"):
        row = q1(
            conn,
            """
            SELECT COUNT(*)
            FROM position_snapshots_latest
            WHERE ABS(COALESCE(signed_qty, 0)) > 1e-12
            """
        )
        active = int(row[0] or 0)
        parts.append(f"active_positions={active}")

    return CheckResult(table, "PASS", " | ".join(parts))


def check_equity_snapshots(conn: duckdb.DuckDBPyConnection) -> CheckResult:
    table = "equity_snapshots"
    if not table_exists(conn, table):
        return CheckResult(table, "FAIL", "table missing")

    total = safe_count(conn, table) or 0
    if total == 0:
        return CheckResult(table, "WARN", "no equity snapshots yet")

    cols = {c: column_exists(conn, table, c) for c in ["snapshot_time", "cash_balance", "market_value", "total_equity", "used_margin"]}
    select_cols = [c for c, ok in cols.items() if ok]
    row = q1(
        conn,
        f"""
        SELECT {", ".join(select_cols)}
        FROM equity_snapshots
        ORDER BY snapshot_time DESC
        LIMIT 1
        """
    )
    if not row:
        return CheckResult(table, "WARN", f"{total} rows, latest row unavailable")

    data = dict(zip(select_cols, row))
    total_equity = float(data.get("total_equity", 0.0) or 0.0)
    used_margin = float(data.get("used_margin", 0.0) or 0.0)
    return CheckResult(
        table,
        "PASS",
        f"{total} rows | total_equity={total_equity:.4f} used_margin={used_margin:.4f}",
    )


def check_market_prices_latest(conn: duckdb.DuckDBPyConnection) -> CheckResult:
    table = "market_prices_latest"
    if not table_exists(conn, table):
        return CheckResult(table, "FAIL", "table missing")

    total = safe_count(conn, table) or 0
    if total == 0:
        return CheckResult(table, "WARN", "no market prices yet")

    parts: list[str] = [f"{total} rows"]
    if column_exists(conn, table, "stale"):
        row = q1(
            conn,
            """
            SELECT COUNT(*)
            FROM market_prices_latest
            WHERE COALESCE(stale, FALSE) = TRUE
            """
        )
        stale_count = int(row[0] or 0)
        parts.append(f"stale={stale_count}")

    return CheckResult(table, "PASS", " | ".join(parts))


def check_position_snapshot_versions(conn: duckdb.DuckDBPyConnection) -> CheckResult:
    table = "position_snapshot_versions"
    if not table_exists(conn, table):
        return CheckResult(table, "FAIL", "table missing")

    total = safe_count(conn, table) or 0
    if total == 0:
        return CheckResult(table, "WARN", "no snapshot versions yet")

    parts: list[str] = [f"{total} rows"]
    if column_exists(conn, table, "build_status"):
        row = q1(
            conn,
            """
            SELECT build_status, COUNT(*)
            FROM position_snapshot_versions
            GROUP BY build_status
            ORDER BY COUNT(*) DESC
            LIMIT 1
            """
        )
        if row:
            parts.append(f"top_status={row[0]}")

    return CheckResult(table, "PASS", " | ".join(parts))


def check_execution_state_snapshots(conn: duckdb.DuckDBPyConnection) -> CheckResult:
    table = "execution_state_snapshots"
    if not table_exists(conn, table):
        return CheckResult(table, "FAIL", "table missing")

    total = safe_count(conn, table) or 0
    if total == 0:
        return CheckResult(table, "WARN", "no execution state snapshots yet")

    return CheckResult(table, "PASS", f"{total} rows")


def check_execution_block_reasons(conn: duckdb.DuckDBPyConnection) -> CheckResult:
    table = "execution_block_reasons"
    if not table_exists(conn, table):
        return CheckResult(table, "FAIL", "table missing")

    total = safe_count(conn, table) or 0
    if total == 0:
        return CheckResult(table, "PASS", "no block reasons recorded")

    parts: list[str] = [f"{total} rows"]
    if column_exists(conn, table, "code"):
        rows = qall(
            conn,
            """
            SELECT code, COUNT(*)
            FROM execution_block_reasons
            GROUP BY code
            ORDER BY COUNT(*) DESC
            LIMIT 5
            """
        )
        parts.append("top_codes=" + ", ".join(f"{code}={cnt}" for code, cnt in rows))
    return CheckResult(table, "WARN", " | ".join(parts))


def print_latest_samples(conn: duckdb.DuckDBPyConnection) -> None:
    samples = [
        ("cash_ledger", "event_time"),
        ("execution_orders", "created_at"),
        ("execution_fills", "created_at"),
        ("equity_snapshots", "snapshot_time"),
        ("position_snapshot_versions", "snapshot_time"),
    ]

    print("\n=== latest sample rows ===")
    for table_name, order_col in samples:
        if not table_exists(conn, table_name):
            continue
        rows = latest_rows(conn, table_name, order_col, limit=3)
        print(f"\n[{table_name}]")
        if not rows:
            print("(no rows or order column unavailable)")
            continue
        for row in rows:
            print(row)


def main() -> int:
    parser = argparse.ArgumentParser(description="Paper trading smoke check for DuckDB")
    parser.add_argument("--db", required=True, help="Path to DuckDB database file")
    parser.add_argument("--show-samples", action="store_true", help="Print sample latest rows")
    args = parser.parse_args()

    conn = duckdb.connect(args.db, read_only=True)

    results: list[CheckResult] = []
    results.extend(check_required_tables(conn))
    results.append(check_cash_ledger(conn))
    results.append(check_execution_orders(conn))
    results.append(check_execution_fills(conn))
    results.append(check_position_snapshots_latest(conn))
    results.append(check_equity_snapshots(conn))
    results.append(check_market_prices_latest(conn))
    results.append(check_position_snapshot_versions(conn))
    results.append(check_execution_state_snapshots(conn))
    results.append(check_execution_block_reasons(conn))

    print("=== paper trading smoke check ===")
    fail_count = 0
    warn_count = 0
    for r in results:
        print(f"[{r.status}] {r.name}: {r.message}")
        if r.status == "FAIL":
            fail_count += 1
        elif r.status == "WARN":
            warn_count += 1

    if args.show_samples:
        print_latest_samples(conn)

    print("\n=== summary ===")
    print(f"FAIL={fail_count} WARN={warn_count} PASS={len(results) - fail_count - warn_count}")

    conn.close()
    return 1 if fail_count > 0 else 0


if __name__ == "__main__":
    sys.exit(main())