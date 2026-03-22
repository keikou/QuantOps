from __future__ import annotations

from pathlib import Path
import json
from typing import Any

try:
    import duckdb  # type: ignore
except Exception:  # pragma: no cover
    duckdb = None
    import sqlite3


class Sprint5DStore:
    def __init__(self, path: Path) -> None:
        self.path = path if duckdb is not None else path.with_suffix('.sqlite3')
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_schema()
        self.seed_default_modes()

    def _conn(self):
        if duckdb is not None:
            return duckdb.connect(str(self.path))
        conn = sqlite3.connect(str(self.path))
        return conn

    def _ensure_schema(self) -> None:
        with self._conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS runtime_mode_configs (
                    mode VARCHAR PRIMARY KEY,
                    is_enabled BOOLEAN,
                    allow_external_send BOOLEAN,
                    require_live_credentials BOOLEAN,
                    require_hard_risk_pass BOOLEAN,
                    updated_at TIMESTAMP
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS runtime_mode_runs (
                    run_id VARCHAR,
                    runtime_mode VARCHAR,
                    source_job_id VARCHAR,
                    trigger_source VARCHAR,
                    mode_policy_json VARCHAR,
                    status VARCHAR,
                    details_json VARCHAR,
                    created_at TIMESTAMP
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS validation_results (
                    validation_id VARCHAR,
                    run_id VARCHAR,
                    runtime_mode VARCHAR,
                    check_name VARCHAR,
                    passed BOOLEAN,
                    severity VARCHAR,
                    details_json VARCHAR,
                    checked_at TIMESTAMP
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS incidents (
                    incident_id VARCHAR,
                    run_id VARCHAR,
                    runtime_mode VARCHAR,
                    category VARCHAR,
                    severity VARCHAR,
                    message VARCHAR,
                    payload_json VARCHAR,
                    created_at TIMESTAMP
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS shadow_pnl_snapshots (
                    run_id VARCHAR,
                    created_at VARCHAR,
                    gross_alpha_pnl_usd DOUBLE,
                    net_shadow_pnl_usd DOUBLE,
                    execution_drag_usd DOUBLE,
                    slippage_drag_usd DOUBLE,
                    fee_drag_usd DOUBLE,
                    latency_drag_usd DOUBLE
                )
            """)

    def seed_default_modes(self) -> None:
        defaults = [
            ('paper', True, False, False, False),
            ('shadow', True, False, False, False),
            ('live_ready', True, False, True, True),
        ]
        with self._conn() as conn:
            for row in defaults:
                mode = row[0]
                exists = conn.execute(
                    "SELECT COUNT(*) FROM runtime_mode_configs WHERE mode = ?",
                    [mode],
                ).fetchone()[0]
                if not exists:
                    conn.execute(
                        """
                        INSERT INTO runtime_mode_configs
                        (mode, is_enabled, allow_external_send, require_live_credentials, require_hard_risk_pass, updated_at)
                        VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                        """,
                        list(row),
                    )

    def list_modes(self) -> list[dict[str, Any]]:
        with self._conn() as conn:
            rows = conn.execute(
                """
                SELECT mode, is_enabled, allow_external_send, require_live_credentials, require_hard_risk_pass, updated_at
                FROM runtime_mode_configs
                ORDER BY mode
                """
            ).fetchall()
        return [
            {
                'mode': row[0],
                'is_enabled': bool(row[1]),
                'allow_external_send': bool(row[2]),
                'require_live_credentials': bool(row[3]),
                'require_hard_risk_pass': bool(row[4]),
                'updated_at': str(row[5]),
            }
            for row in rows
        ]

    def get_mode(self, mode: str) -> dict[str, Any] | None:
        with self._conn() as conn:
            row = conn.execute(
                """
                SELECT mode, is_enabled, allow_external_send, require_live_credentials, require_hard_risk_pass, updated_at
                FROM runtime_mode_configs
                WHERE mode = ?
                """,
                [mode],
            ).fetchone()
        if not row:
            return None
        return {
            'mode': row[0],
            'is_enabled': bool(row[1]),
            'allow_external_send': bool(row[2]),
            'require_live_credentials': bool(row[3]),
            'require_hard_risk_pass': bool(row[4]),
            'updated_at': str(row[5]),
        }

    def update_mode(self, mode: str, is_enabled: bool = True) -> dict[str, Any]:
        with self._conn() as conn:
            conn.execute(
                """
                UPDATE runtime_mode_configs
                SET is_enabled = ?, updated_at = CURRENT_TIMESTAMP
                WHERE mode = ?
                """,
                [is_enabled, mode],
            )
        return self.get_mode(mode) or {'mode': mode, 'is_enabled': is_enabled}

    def insert_run(self, row: dict[str, Any]) -> None:
        with self._conn() as conn:
            conn.execute(
                """
                INSERT INTO runtime_mode_runs
                (run_id, runtime_mode, source_job_id, trigger_source, mode_policy_json, status, details_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    row['run_id'],
                    row['runtime_mode'],
                    row.get('source_job_id'),
                    row.get('trigger_source'),
                    json.dumps(row.get('mode_policy', {}), ensure_ascii=False),
                    row.get('status', 'ok'),
                    json.dumps(row.get('details', {}), ensure_ascii=False),
                    row['created_at'],
                ],
            )

    def latest_run(self) -> dict[str, Any]:
        with self._conn() as conn:
            row = conn.execute(
                """
                SELECT run_id, runtime_mode, source_job_id, trigger_source, mode_policy_json, status, details_json, created_at
                FROM runtime_mode_runs
                ORDER BY created_at DESC
                LIMIT 1
                """
            ).fetchone()
        if not row:
            return {'status': 'missing'}
        return {
            'run_id': row[0],
            'runtime_mode': row[1],
            'source_job_id': row[2],
            'trigger_source': row[3],
            'mode_policy': json.loads(row[4] or '{}'),
            'status': row[5],
            'details': json.loads(row[6] or '{}'),
            'created_at': str(row[7]),
        }

    def insert_validation(self, row: dict[str, Any]) -> None:
        with self._conn() as conn:
            conn.execute(
                """
                INSERT INTO validation_results
                (validation_id, run_id, runtime_mode, check_name, passed, severity, details_json, checked_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    row['validation_id'],
                    row['run_id'],
                    row['runtime_mode'],
                    row['check_name'],
                    row['passed'],
                    row['severity'],
                    json.dumps(row.get('details', {}), ensure_ascii=False),
                    row['checked_at'],
                ],
            )

    def list_validations(self, run_id: str | None = None) -> list[dict[str, Any]]:
        query = """
            SELECT validation_id, run_id, runtime_mode, check_name, passed, severity, details_json, checked_at
            FROM validation_results
        """
        params: list[Any] = []
        if run_id:
            query += " WHERE run_id = ?"
            params.append(run_id)
        query += " ORDER BY checked_at DESC"
        with self._conn() as conn:
            rows = conn.execute(query, params).fetchall()
        return [
            {
                'validation_id': row[0],
                'run_id': row[1],
                'runtime_mode': row[2],
                'check_name': row[3],
                'passed': bool(row[4]),
                'severity': row[5],
                'details': json.loads(row[6] or '{}'),
                'checked_at': str(row[7]),
            }
            for row in rows
        ]

    def insert_incident(self, row: dict[str, Any]) -> None:
        with self._conn() as conn:
            conn.execute(
                """
                INSERT INTO incidents
                (incident_id, run_id, runtime_mode, category, severity, message, payload_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    row['incident_id'],
                    row['run_id'],
                    row['runtime_mode'],
                    row['category'],
                    row['severity'],
                    row['message'],
                    json.dumps(row.get('payload', {}), ensure_ascii=False),
                    row['created_at'],
                ],
            )

    def latest_incidents(self, limit: int = 20) -> list[dict[str, Any]]:
        with self._conn() as conn:
            rows = conn.execute(
                """
                SELECT incident_id, run_id, runtime_mode, category, severity, message, payload_json, created_at
                FROM incidents
                ORDER BY created_at DESC
                LIMIT ?
                """,
                [limit],
            ).fetchall()
        return [
            {
                'incident_id': row[0],
                'run_id': row[1],
                'runtime_mode': row[2],
                'category': row[3],
                'severity': row[4],
                'message': row[5],
                'payload': json.loads(row[6] or '{}'),
                'created_at': str(row[7]),
            }
            for row in rows
        ]

    def insert_shadow_snapshot(self, row: dict[str, Any]) -> None:
        with self._conn() as conn:
            conn.execute(
                """
                INSERT INTO shadow_pnl_snapshots
                (run_id, created_at, gross_alpha_pnl_usd, net_shadow_pnl_usd, execution_drag_usd, slippage_drag_usd, fee_drag_usd, latency_drag_usd)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    row['run_id'],
                    row['created_at'],
                    row['gross_alpha_pnl'],
                    row['net_shadow_pnl'],
                    row['execution_drag'],
                    row['slippage_drag'],
                    row['fee_drag'],
                    row['latency_drag'],
                ],
            )

    def latest_shadow_summary(self) -> dict[str, Any]:
        with self._conn() as conn:
            row = conn.execute(
                """
                SELECT run_id, created_at, gross_alpha_pnl_usd, net_shadow_pnl_usd, execution_drag_usd, slippage_drag_usd, fee_drag_usd, latency_drag_usd
                FROM shadow_pnl_snapshots
                ORDER BY created_at DESC
                LIMIT 1
                """
            ).fetchone()
        if not row:
            return {'status': 'missing'}
        return {
            'run_id': row[0],
            'timestamp': row[1],
            'gross_alpha_pnl': float(row[2]),
            'net_shadow_pnl': float(row[3]),
            'execution_drag': float(row[4]),
            'slippage_drag': float(row[5]),
            'fee_drag': float(row[6]),
            'latency_drag': float(row[7]),
        }
