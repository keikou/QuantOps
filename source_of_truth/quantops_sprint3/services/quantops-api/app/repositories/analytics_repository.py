from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from app.repositories.duckdb import DuckDBConnectionFactory


class AnalyticsRepository:
    def __init__(self, factory: DuckDBConnectionFactory) -> None:
        self.factory = factory

    def insert_alpha_snapshot(self, rows: list[dict]) -> list[dict]:
        now = datetime.now(timezone.utc)
        with self.factory.connect() as conn:
            for row in rows:
                conn.execute(
                    """
                    INSERT INTO alpha_performance_snapshots(
                        snapshot_id, strategy_id, strategy_name, pnl, sharpe, drawdown, hit_rate, turnover, rank_score, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    [
                        f"alpha-{uuid4()}",
                        row["strategy_id"],
                        row["strategy_name"],
                        row["pnl"],
                        row["sharpe"],
                        row["drawdown"],
                        row["hit_rate"],
                        row["turnover"],
                        row["rank_score"],
                        now,
                    ],
                )
        return rows

    def insert_execution_snapshot(self, row: dict) -> dict:
        now = datetime.now(timezone.utc)
        with self.factory.connect() as conn:
            conn.execute(
                """
                INSERT INTO execution_quality_snapshots(
                    snapshot_id, fill_rate, avg_slippage_bps, latency_ms_p50, latency_ms_p95, venue_score, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    f"exec-{uuid4()}",
                    row["fill_rate"], row["avg_slippage_bps"], row["latency_ms_p50"], row["latency_ms_p95"], row["venue_score"], now
                ],
            )
        return row

    def latest_alpha_rows(self) -> list[dict]:
        query = """
        WITH ranked AS (
            SELECT *,
                   ROW_NUMBER() OVER (PARTITION BY strategy_id ORDER BY created_at DESC) AS rn
            FROM alpha_performance_snapshots
        )
        SELECT strategy_id, strategy_name, pnl, sharpe, drawdown, hit_rate, turnover, rank_score, CAST(created_at AS VARCHAR)
        FROM ranked
        WHERE rn = 1
        ORDER BY rank_score DESC, sharpe DESC
        """
        with self.factory.connect(read_only=True) as conn:
            rows = conn.execute(query).fetchall()
        return [
            {
                "strategy_id": r[0], "strategy_name": r[1], "pnl": r[2], "sharpe": r[3], "drawdown": r[4],
                "hit_rate": r[5], "turnover": r[6], "rank_score": r[7], "as_of": r[8]
            }
            for r in rows
        ]

    def latest_execution(self) -> dict | None:
        with self.factory.connect(read_only=True) as conn:
            row = conn.execute(
                """
                SELECT fill_rate, avg_slippage_bps, latency_ms_p50, latency_ms_p95, venue_score, CAST(created_at AS VARCHAR)
                FROM execution_quality_snapshots
                ORDER BY created_at DESC LIMIT 1
                """
            ).fetchone()
        if row is None:
            return None
        return {
            "fill_rate": row[0], "avg_slippage_bps": row[1], "latency_ms_p50": row[2], "latency_ms_p95": row[3], "venue_score": row[4], "as_of": row[5]
        }

    def pnl_series(self) -> list[dict]:
        with self.factory.connect(read_only=True) as conn:
            rows = conn.execute(
                """
                SELECT CAST(created_at AS VARCHAR) AS ts, ROUND(SUM(pnl), 6) AS pnl
                FROM alpha_performance_snapshots
                GROUP BY ts
                ORDER BY ts DESC
                LIMIT 20
                """
            ).fetchall()
        return [{"ts": r[0], "pnl": r[1]} for r in rows][::-1]

    def drawdown_series(self) -> list[dict]:
        with self.factory.connect(read_only=True) as conn:
            rows = conn.execute(
                """
                SELECT CAST(created_at AS VARCHAR) AS ts, ROUND(MAX(drawdown), 6) AS drawdown
                FROM alpha_performance_snapshots
                GROUP BY ts
                ORDER BY ts DESC
                LIMIT 20
                """
            ).fetchall()
        return [{"ts": r[0], "drawdown": r[1]} for r in rows][::-1]

    def runtime_states(self) -> list[dict]:
        with self.factory.connect(read_only=True) as conn:
            rows = conn.execute(
                """
                SELECT strategy_id, desired_state, remote_status, note, CAST(updated_at AS VARCHAR)
                FROM strategy_runtime_state
                ORDER BY strategy_id
                """
            ).fetchall()
        return [
            {"strategy_id": r[0], "desired_state": r[1], "remote_status": r[2], "note": r[3], "updated_at": r[4]}
            for r in rows
        ]

    def upsert_runtime_state(self, strategy_id: str, desired_state: str, remote_status: str, note: str) -> dict:
        now = datetime.now(timezone.utc)
        with self.factory.connect() as conn:
            conn.execute(
                """
                INSERT INTO strategy_runtime_state(strategy_id, desired_state, remote_status, note, updated_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(strategy_id) DO UPDATE SET
                    desired_state=excluded.desired_state,
                    remote_status=excluded.remote_status,
                    note=excluded.note,
                    updated_at=excluded.updated_at
                """,
                [strategy_id, desired_state, remote_status, note, now],
            )
        return {"strategy_id": strategy_id, "desired_state": desired_state, "remote_status": remote_status, "note": note, "updated_at": now.isoformat()}
