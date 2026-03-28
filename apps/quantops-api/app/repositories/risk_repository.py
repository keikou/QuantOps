from __future__ import annotations

import ast
from datetime import datetime, timezone
from uuid import uuid4

from app.repositories.duckdb import DuckDBConnectionFactory


class RiskRepository:
    def __init__(self, factory: DuckDBConnectionFactory) -> None:
        self.factory = factory

    def _table_exists(self, conn, table_name: str) -> bool:
        try:
            tables = {r[0] for r in conn.execute("SHOW TABLES").fetchall()}
            return table_name in tables
        except Exception:
            row = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name = ?",
                [table_name],
            ).fetchone()
            return row is not None

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
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS risk_control_state(
                state_id VARCHAR,
                trading_state VARCHAR,
                note VARCHAR,
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
                if not self._table_exists(conn, 'risk_snapshots'):
                    return None
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

        alert_state = row[7] or "unknown"
        state = self.get_trading_state()
        trading_state = state.get("trading_state", "running")
        if alert_state == "breach" and trading_state == "running":
            trading_state = "halted"
        kill_switch = "triggered" if alert_state == "breach" else "armed" if alert_state == "warning" else "normal"
        return {
            "gross_exposure": row[0] if row[0] is not None else 0.0,
            "net_exposure": row[1] if row[1] is not None else 0.0,
            "leverage": row[2] if row[2] is not None else 0.0,
            "drawdown": row[3] if row[3] is not None else 0.0,
            "var_95": row[4],
            "stress_loss": row[5],
            "risk_limit": risk_limit if isinstance(risk_limit, dict) else {},
            "alert_state": alert_state,
            "alert": alert_state,
            "kill_switch": kill_switch,
            "trading_state": trading_state,
            "state_note": state.get("note", ""),
            "as_of": row[8] or datetime.now(timezone.utc).isoformat(),
        }


    def set_trading_state(self, trading_state: str, note: str = '') -> dict:
        state_id = f"riskctl-{uuid4()}"
        now = datetime.now(timezone.utc)
        with self.factory.connect() as conn:
            self._ensure_tables(conn)
            conn.execute(
                "INSERT INTO risk_control_state(state_id, trading_state, note, created_at) VALUES (?, ?, ?, ?)",
                [state_id, trading_state, note, now],
            )
        return {"state_id": state_id, "trading_state": trading_state, "note": note, "as_of": now.isoformat()}

    def get_trading_state(self) -> dict:
        try:
            with self.factory.connect(read_only=True) as conn:
                if not self._table_exists(conn, 'risk_control_state'):
                    row = None
                else:
                    row = conn.execute(
                        "SELECT state_id, trading_state, note, CAST(created_at AS VARCHAR) FROM risk_control_state ORDER BY created_at DESC LIMIT 1"
                    ).fetchone()
        except Exception:
            row = None
        if row is None:
            return {"state_id": None, "trading_state": "running", "note": "", "as_of": datetime.now(timezone.utc).isoformat()}
        return {"state_id": row[0], "trading_state": row[1] or "running", "note": row[2] or "", "as_of": row[3] or datetime.now(timezone.utc).isoformat()}
