from __future__ import annotations

import ast
from datetime import datetime, timezone
from uuid import uuid4

from app.repositories.duckdb import DuckDBConnectionFactory


class RiskRepository:
    def __init__(self, factory: DuckDBConnectionFactory) -> None:
        self.factory = factory

    def _ensure_tables(self, conn) -> None:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS risk_snapshots(
                snapshot_id VARCHAR,
                gross_exposure DOUBLE,
                net_exposure DOUBLE,
                leverage DOUBLE,
                drawdown DOUBLE,
                var_95 DOUBLE,
                stress_loss DOUBLE,
                risk_limit_json VARCHAR,
                alert_state VARCHAR,
                created_at TIMESTAMP
            )
            """
        )

    def insert_snapshot(self, snapshot: dict) -> dict:
        snapshot_id = f"risk-{uuid4()}"
        with self.factory.connect() as conn:
            self._ensure_tables(conn)
            conn.execute(
                """
                INSERT INTO risk_snapshots(
                    snapshot_id, gross_exposure, net_exposure, leverage, drawdown,
                    var_95, stress_loss, risk_limit_json, alert_state, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    snapshot_id,
                    snapshot["gross_exposure"],
                    snapshot["net_exposure"],
                    snapshot["leverage"],
                    snapshot["drawdown"],
                    snapshot.get("var_95"),
                    snapshot.get("stress_loss"),
                    str(snapshot.get("risk_limit", {})),
                    snapshot["alert_state"],
                    datetime.now(timezone.utc),
                ],
            )
        return snapshot

    def latest_snapshot(self) -> dict | None:
        try:
            with self.factory.connect(read_only=True) as conn:
                self._ensure_tables(conn)
                row = conn.execute(
                    """
                    SELECT gross_exposure, net_exposure, leverage, drawdown, var_95,
                           stress_loss, risk_limit_json, alert_state, CAST(created_at AS VARCHAR)
                    FROM risk_snapshots
                    ORDER BY created_at DESC
                    LIMIT 1
                    """
                ).fetchone()
        except Exception:
            return None

        if row is None:
            return None

        risk_limit = row[6]
        if isinstance(risk_limit, str):
            try:
                risk_limit = ast.literal_eval(risk_limit)
            except Exception:
                risk_limit = {"raw": risk_limit}

        return {
            "gross_exposure": row[0] if row[0] is not None else 0.0,
            "net_exposure": row[1] if row[1] is not None else 0.0,
            "leverage": row[2] if row[2] is not None else 0.0,
            "drawdown": row[3] if row[3] is not None else 0.0,
            "var_95": row[4],
            "stress_loss": row[5],
            "risk_limit": risk_limit if isinstance(risk_limit, dict) else {},
            "alert_state": row[7] or "unknown",
            "as_of": row[8] or datetime.now(timezone.utc).isoformat(),
        }
