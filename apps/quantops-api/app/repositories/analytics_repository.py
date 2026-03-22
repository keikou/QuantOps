from __future__ import annotations

import json
from datetime import datetime, timezone
from uuid import uuid4

from app.clients.v12_client import utc_now_iso
from app.repositories.duckdb import DuckDBConnectionFactory


class AnalyticsRepository:
    def __init__(self, factory: DuckDBConnectionFactory) -> None:
        self.factory = factory

    def _has_table(self, conn, table_name: str) -> bool:
        try:
            return table_name in {row[0] for row in conn.execute("SHOW TABLES").fetchall()}
        except Exception:
            row = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name = ?",
                [table_name],
            ).fetchone()
            return row is not None

    def _table_columns(self, conn, table_name: str) -> list[str]:
        if not self._has_table(conn, table_name):
            return []
        return [row[1] for row in conn.execute(f"PRAGMA table_info('{table_name}')").fetchall()]

    def _rebuild_alpha_table_if_legacy(self, conn) -> None:
        columns = self._table_columns(conn, "alpha_performance_snapshots")
        expected = {
            "snapshot_id",
            "strategy_id",
            "strategy_name",
            "pnl",
            "sharpe",
            "drawdown",
            "hit_rate",
            "turnover",
            "rank_score",
            "created_at",
        }
        legacy = {
            "snapshot_id",
            "alpha_name",
            "pnl",
            "sharpe",
            "win_rate",
            "trades",
            "created_at",
        }

        if not columns:
            return
        if set(columns) == expected:
            return
        if set(columns) == legacy:
            conn.execute("ALTER TABLE alpha_performance_snapshots RENAME TO alpha_performance_snapshots_legacy")
            self._create_alpha_table(conn)
            conn.execute(
                """
                INSERT INTO alpha_performance_snapshots(
                    snapshot_id,
                    strategy_id,
                    strategy_name,
                    pnl,
                    sharpe,
                    drawdown,
                    hit_rate,
                    turnover,
                    rank_score,
                    created_at
                )
                SELECT
                    snapshot_id,
                    COALESCE(alpha_name, 'legacy'),
                    COALESCE(alpha_name, 'legacy'),
                    COALESCE(pnl, 0.0),
                    COALESCE(sharpe, 0.0),
                    0.0,
                    COALESCE(win_rate, 0.0),
                    0.0,
                    COALESCE(sharpe, 0.0),
                    COALESCE(created_at, CURRENT_TIMESTAMP)
                FROM alpha_performance_snapshots_legacy
                """
            )
            return

        conn.execute("DROP TABLE IF EXISTS alpha_performance_snapshots")
        self._create_alpha_table(conn)

    def _rebuild_execution_table_if_legacy(self, conn) -> None:
        columns = self._table_columns(conn, "execution_quality_snapshots")
        expected = {
            "snapshot_id",
            "fill_rate",
            "avg_slippage_bps",
            "latency_ms_p50",
            "latency_ms_p95",
            "venue_score",
            "created_at",
        }
        legacy = {"snapshot_id", "payload", "created_at"}

        if not columns:
            return
        if set(columns) == expected:
            return
        if set(columns) == legacy:
            conn.execute("ALTER TABLE execution_quality_snapshots RENAME TO execution_quality_snapshots_legacy")
            self._create_execution_table(conn)
            return

        conn.execute("DROP TABLE IF EXISTS execution_quality_snapshots")
        self._create_execution_table(conn)

    def _create_alpha_table(self, conn) -> None:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS alpha_performance_snapshots(
                snapshot_id VARCHAR PRIMARY KEY,
                strategy_id VARCHAR NOT NULL,
                strategy_name VARCHAR NOT NULL,
                pnl DOUBLE NOT NULL,
                sharpe DOUBLE NOT NULL,
                drawdown DOUBLE NOT NULL,
                hit_rate DOUBLE NOT NULL,
                turnover DOUBLE NOT NULL,
                rank_score DOUBLE NOT NULL,
                created_at TIMESTAMP NOT NULL
            )
            """
        )

    def _create_execution_table(self, conn) -> None:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS execution_quality_snapshots(
                snapshot_id VARCHAR PRIMARY KEY,
                fill_rate DOUBLE NOT NULL,
                avg_slippage_bps DOUBLE NOT NULL,
                latency_ms_p50 DOUBLE NOT NULL,
                latency_ms_p95 DOUBLE NOT NULL,
                venue_score DOUBLE NOT NULL,
                created_at TIMESTAMP NOT NULL
            )
            """
        )

    def _create_runtime_table(self, conn) -> None:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS strategy_runtime_state(
                strategy_id VARCHAR PRIMARY KEY,
                desired_state VARCHAR NOT NULL,
                remote_status VARCHAR NOT NULL,
                note VARCHAR,
                updated_at TIMESTAMP NOT NULL
            )
            """
        )

    def _create_strategy_overrides_table(self, conn) -> None:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS strategy_overrides(
                strategy_id VARCHAR PRIMARY KEY,
                risk_budget DOUBLE,
                capital_allocation DOUBLE,
                note VARCHAR,
                updated_at TIMESTAMP NOT NULL
            )
            """
        )

    def _create_portfolio_table(self, conn) -> None:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS portfolio_diagnostics_snapshots(
                snapshot_id VARCHAR PRIMARY KEY,
                payload VARCHAR,
                created_at TIMESTAMP NOT NULL
            )
            """
        )

    def _ensure_tables(self, conn) -> None:
        self._create_alpha_table(conn)
        self._create_execution_table(conn)
        self._create_runtime_table(conn)
        self._create_strategy_overrides_table(conn)
        self._create_portfolio_table(conn)
        self._rebuild_alpha_table_if_legacy(conn)
        self._rebuild_execution_table_if_legacy(conn)

    def insert_alpha_snapshot(self, rows: list[dict]) -> list[dict]:
        if not rows:
            return rows

        with self.factory.connect() as conn:
            self._ensure_tables(conn)
            now = datetime.now(timezone.utc)
            for row in rows:
                conn.execute(
                    """
                    INSERT INTO alpha_performance_snapshots(
                        snapshot_id,
                        strategy_id,
                        strategy_name,
                        pnl,
                        sharpe,
                        drawdown,
                        hit_rate,
                        turnover,
                        rank_score,
                        created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    [
                        f"alpha-{uuid4()}",
                        row.get("strategy_id", "unknown"),
                        row.get("strategy_name", row.get("strategy_id", "unknown")),
                        float(row.get("pnl", 0.0) or 0.0),
                        float(row.get("sharpe", 0.0) or 0.0),
                        float(row.get("drawdown", 0.0) or 0.0),
                        float(row.get("hit_rate", 0.0) or 0.0),
                        float(row.get("turnover", 0.0) or 0.0),
                        float(row.get("rank_score", 0.0) or 0.0),
                        now,
                    ],
                )
        return rows

    def insert_execution_snapshot(self, payload: dict) -> dict:
        with self.factory.connect() as conn:
            self._ensure_tables(conn)
            conn.execute(
                """
                INSERT INTO execution_quality_snapshots(
                    snapshot_id,
                    fill_rate,
                    avg_slippage_bps,
                    latency_ms_p50,
                    latency_ms_p95,
                    venue_score,
                    created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    f"exec-{uuid4()}",
                    float(payload.get("fill_rate", 0.0) or 0.0),
                    float(payload.get("avg_slippage_bps", 0.0) or 0.0),
                    float(payload.get("latency_ms_p50", 0.0) or 0.0),
                    float(payload.get("latency_ms_p95", 0.0) or 0.0),
                    float(payload.get("venue_score", 0.0) or 0.0),
                    datetime.now(timezone.utc),
                ],
            )
        return payload

    def insert_portfolio_diagnostics_snapshot(self, payload: dict) -> dict:
        with self.factory.connect() as conn:
            self._ensure_tables(conn)
            conn.execute(
                """
                INSERT INTO portfolio_diagnostics_snapshots(
                    snapshot_id, payload, created_at
                ) VALUES (?, ?, ?)
                """,
                [f"portfolio-{uuid4()}", json.dumps(payload, ensure_ascii=False), datetime.now(timezone.utc)],
            )
        return payload

    def latest_alpha_rows(self) -> list[dict]:
        with self.factory.connect(read_only=True) as conn:
            if not self._has_table(conn, "strategy_runtime_state"):
                return []
            rows = conn.execute(
                """
                WITH latest_per_strategy AS (
                    SELECT
                        strategy_id,
                        MAX(created_at) AS latest_created_at
                    FROM alpha_performance_snapshots
                    GROUP BY strategy_id
                )
                SELECT
                    a.strategy_id,
                    a.strategy_name,
                    a.pnl,
                    a.sharpe,
                    a.drawdown,
                    a.hit_rate,
                    a.turnover,
                    a.rank_score,
                    CAST(a.created_at AS VARCHAR)
                FROM alpha_performance_snapshots a
                JOIN latest_per_strategy l
                  ON a.strategy_id = l.strategy_id
                 AND a.created_at = l.latest_created_at
                ORDER BY a.rank_score DESC, a.sharpe DESC, a.strategy_id ASC
                """
            ).fetchall()

        return [
            {
                "strategy_id": row[0],
                "strategy_name": row[1],
                "pnl": float(row[2]),
                "sharpe": float(row[3]),
                "drawdown": float(row[4]),
                "hit_rate": float(row[5]),
                "turnover": float(row[6]),
                "rank_score": float(row[7]),
                "as_of": row[8] or utc_now_iso(),
            }
            for row in rows
        ]

    def pnl_series(self, limit: int = 100) -> list[dict]:
        with self.factory.connect(read_only=True) as conn:
            if not self._has_table(conn, "strategy_runtime_state"):
                return []
            rows = conn.execute(
                """
                SELECT
                    CAST(created_at AS VARCHAR) AS as_of,
                    SUM(pnl) AS total_pnl
                FROM alpha_performance_snapshots
                GROUP BY created_at
                ORDER BY created_at DESC
                LIMIT ?
                """,
                [limit],
            ).fetchall()

        return [{"as_of": row[0] or utc_now_iso(), "total_pnl": float(row[1] or 0.0)} for row in reversed(rows)]

    def drawdown_series(self, limit: int = 100) -> list[dict]:
        with self.factory.connect(read_only=True) as conn:
            if not self._has_table(conn, "strategy_runtime_state"):
                return []
            rows = conn.execute(
                """
                SELECT
                    CAST(created_at AS VARCHAR) AS as_of,
                    MAX(drawdown) AS max_drawdown
                FROM alpha_performance_snapshots
                GROUP BY created_at
                ORDER BY created_at DESC
                LIMIT ?
                """,
                [limit],
            ).fetchall()

        return [{"as_of": row[0] or utc_now_iso(), "max_drawdown": float(row[1] or 0.0)} for row in reversed(rows)]

    def latest_execution(self) -> dict | None:
        with self.factory.connect(read_only=True) as conn:
            if not self._has_table(conn, "execution_quality_snapshots"):
                return None
            row = conn.execute(
                """
                SELECT
                    fill_rate,
                    avg_slippage_bps,
                    latency_ms_p50,
                    latency_ms_p95,
                    venue_score,
                    CAST(created_at AS VARCHAR)
                FROM execution_quality_snapshots
                ORDER BY created_at DESC
                LIMIT 1
                """
            ).fetchone()

        if row is None:
            return None

        return {
            "fill_rate": float(row[0] or 0.0),
            "avg_slippage_bps": float(row[1] or 0.0),
            "latency_ms_p50": float(row[2] or 0.0),
            "latency_ms_p95": float(row[3] or 0.0),
            "venue_score": float(row[4] or 0.0),
            "as_of": row[5] or utc_now_iso(),
        }

    def upsert_runtime_state(self, strategy_id: str, desired_state: str, remote_status: str, note: str | None = None) -> dict:
        now = datetime.now(timezone.utc)
        with self.factory.connect() as conn:
            self._ensure_tables(conn)
            conn.execute(
                """
                INSERT OR REPLACE INTO strategy_runtime_state(
                    strategy_id, desired_state, remote_status, note, updated_at
                ) VALUES (?, ?, ?, ?, ?)
                """,
                [strategy_id, desired_state, remote_status, note, now],
            )

        return {
            "strategy_id": strategy_id,
            "desired_state": desired_state,
            "remote_status": remote_status,
            "note": note,
            "updated_at": now.isoformat(),
        }

    def runtime_states(self) -> list[dict]:
        with self.factory.connect(read_only=True) as conn:
            if not self._has_table(conn, "strategy_runtime_state"):
                return []
            rows = conn.execute(
                """
                SELECT strategy_id, desired_state, remote_status, note, CAST(updated_at AS VARCHAR)
                FROM strategy_runtime_state
                ORDER BY updated_at DESC, strategy_id ASC
                """
            ).fetchall()

        return [
            {
                "strategy_id": row[0],
                "desired_state": row[1],
                "remote_status": row[2],
                "note": row[3],
                "updated_at": row[4] or utc_now_iso(),
            }
            for row in rows
        ]


    def upsert_strategy_override(
        self,
        *,
        strategy_id: str,
        risk_budget: float | None = None,
        capital_allocation: float | None = None,
        note: str | None = None,
    ) -> dict:
        now = datetime.now(timezone.utc)
        with self.factory.connect() as conn:
            self._ensure_tables(conn)
            existing = conn.execute(
                "SELECT risk_budget, capital_allocation, note FROM strategy_overrides WHERE strategy_id = ?",
                [strategy_id],
            ).fetchone()
            next_risk_budget = float(risk_budget) if risk_budget is not None else float(existing[0]) if existing and existing[0] is not None else None
            next_capital_allocation = float(capital_allocation) if capital_allocation is not None else float(existing[1]) if existing and existing[1] is not None else None
            next_note = note if note is not None else existing[2] if existing else None
            conn.execute(
                """
                INSERT OR REPLACE INTO strategy_overrides(
                    strategy_id, risk_budget, capital_allocation, note, updated_at
                ) VALUES (?, ?, ?, ?, ?)
                """,
                [strategy_id, next_risk_budget, next_capital_allocation, next_note, now],
            )
        return {
            "strategy_id": strategy_id,
            "risk_budget": next_risk_budget,
            "capital_allocation": next_capital_allocation,
            "note": next_note,
            "updated_at": now.isoformat(),
        }

    def strategy_overrides(self) -> list[dict]:
        with self.factory.connect(read_only=True) as conn:
            if not self._has_table(conn, "strategy_overrides"):
                return []
            rows = conn.execute(
                """
                SELECT strategy_id, risk_budget, capital_allocation, note, CAST(updated_at AS VARCHAR)
                FROM strategy_overrides
                ORDER BY updated_at DESC, strategy_id ASC
                """
            ).fetchall()
        return [
            {
                "strategy_id": row[0],
                "risk_budget": float(row[1]) if row[1] is not None else None,
                "capital_allocation": float(row[2]) if row[2] is not None else None,
                "note": row[3],
                "updated_at": row[4] or utc_now_iso(),
            }
            for row in rows
        ]
