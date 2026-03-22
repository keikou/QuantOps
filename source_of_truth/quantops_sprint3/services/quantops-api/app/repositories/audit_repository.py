from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from app.repositories.duckdb import DuckDBConnectionFactory


class AuditRepository:
    def __init__(self, factory: DuckDBConnectionFactory) -> None:
        self.factory = factory

    def _ensure_tables(self, conn) -> None:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS audit_logs(
                log_id VARCHAR,
                category VARCHAR,
                actor_id VARCHAR,
                actor_role VARCHAR,
                event_type VARCHAR,
                ref_type VARCHAR,
                ref_id VARCHAR,
                payload_json VARCHAR,
                created_at TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS operator_actions(
                action_id VARCHAR,
                user_id VARCHAR,
                role_name VARCHAR,
                action_type VARCHAR,
                target_type VARCHAR,
                target_id VARCHAR,
                request_json VARCHAR,
                result_status VARCHAR,
                created_at TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS config_change_logs(
                change_id VARCHAR,
                actor_id VARCHAR,
                config_scope VARCHAR,
                payload_json VARCHAR,
                created_at TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS mode_switch_logs(
                switch_id VARCHAR,
                actor_id VARCHAR,
                from_mode VARCHAR,
                to_mode VARCHAR,
                note VARCHAR,
                created_at TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS kill_switch_events(
                event_id VARCHAR,
                actor_id VARCHAR,
                status VARCHAR,
                note VARCHAR,
                created_at TIMESTAMP
            )
            """
        )

    def log_action(self, *, category: str, event_type: str, payload_json: str, actor_id: str = "operator") -> None:
        with self.factory.connect() as conn:
            self._ensure_tables(conn)
            conn.execute(
                """
                INSERT INTO audit_logs(
                    log_id, category, actor_id, actor_role, event_type, ref_type, ref_id, payload_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [f"log-{uuid4()}", category, actor_id, "operator", event_type, None, None, payload_json, datetime.now(timezone.utc)],
            )

    def list_audit_logs(self) -> list[dict]:
        try:
            with self.factory.connect(read_only=True) as conn:
                self._ensure_tables(conn)
                rows = conn.execute(
                    "SELECT category, actor_id, actor_role, event_type, ref_type, ref_id, payload_json, CAST(created_at AS VARCHAR) FROM audit_logs ORDER BY created_at DESC LIMIT 100"
                ).fetchall()
        except Exception:
            return []
        return [{"category": r[0], "actor_id": r[1], "actor_role": r[2], "event_type": r[3], "ref_type": r[4], "ref_id": r[5], "payload_json": r[6], "created_at": r[7]} for r in rows]

    def list_operator_actions(self) -> list[dict]:
        try:
            with self.factory.connect(read_only=True) as conn:
                self._ensure_tables(conn)
                rows = conn.execute(
                    "SELECT action_id, user_id, role_name, action_type, target_type, target_id, request_json, result_status, CAST(created_at AS VARCHAR) FROM operator_actions ORDER BY created_at DESC LIMIT 100"
                ).fetchall()
        except Exception:
            return []
        return [{"action_id": r[0], "user_id": r[1], "role_name": r[2], "action_type": r[3], "target_type": r[4], "target_id": r[5], "request_json": r[6], "result_status": r[7], "created_at": r[8]} for r in rows]

    def log_operator_action(self, *, action_type: str, target_type: str, target_id: str, result_status: str = "ok", request_json: str = "{}", user_id: str = "operator", role_name: str = "operator") -> None:
        with self.factory.connect() as conn:
            self._ensure_tables(conn)
            conn.execute(
                "INSERT INTO operator_actions(action_id, user_id, role_name, action_type, target_type, target_id, request_json, result_status, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                [f"act-{uuid4()}", user_id, role_name, action_type, target_type, target_id, request_json, result_status, datetime.now(timezone.utc)],
            )

    def log_config_change(self, *, config_scope: str, payload_json: str, actor_id: str = "operator") -> None:
        with self.factory.connect() as conn:
            self._ensure_tables(conn)
            conn.execute(
                "INSERT INTO config_change_logs(change_id, actor_id, config_scope, payload_json, created_at) VALUES (?, ?, ?, ?, ?)",
                [f"cfg-{uuid4()}", actor_id, config_scope, payload_json, datetime.now(timezone.utc)],
            )

    def list_config_changes(self) -> list[dict]:
        try:
            with self.factory.connect(read_only=True) as conn:
                self._ensure_tables(conn)
                rows = conn.execute(
                    "SELECT change_id, actor_id, config_scope, payload_json, CAST(created_at AS VARCHAR) FROM config_change_logs ORDER BY created_at DESC LIMIT 100"
                ).fetchall()
        except Exception:
            return []
        return [{"change_id": r[0], "actor_id": r[1], "config_scope": r[2], "payload_json": r[3], "created_at": r[4]} for r in rows]

    def log_mode_switch(self, *, from_mode: str, to_mode: str, note: str = '', actor_id: str = "operator") -> None:
        with self.factory.connect() as conn:
            self._ensure_tables(conn)
            conn.execute(
                "INSERT INTO mode_switch_logs(switch_id, actor_id, from_mode, to_mode, note, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                [f"mode-{uuid4()}", actor_id, from_mode, to_mode, note, datetime.now(timezone.utc)],
            )

    def list_mode_switches(self) -> list[dict]:
        try:
            with self.factory.connect(read_only=True) as conn:
                self._ensure_tables(conn)
                rows = conn.execute(
                    "SELECT switch_id, actor_id, from_mode, to_mode, note, CAST(created_at AS VARCHAR) FROM mode_switch_logs ORDER BY created_at DESC LIMIT 100"
                ).fetchall()
        except Exception:
            return []
        return [{"switch_id": r[0], "actor_id": r[1], "from_mode": r[2], "to_mode": r[3], "note": r[4], "created_at": r[5]} for r in rows]

    def log_kill_switch(self, *, status: str, note: str = '', actor_id: str = "operator") -> None:
        with self.factory.connect() as conn:
            self._ensure_tables(conn)
            conn.execute(
                "INSERT INTO kill_switch_events(event_id, actor_id, status, note, created_at) VALUES (?, ?, ?, ?, ?)",
                [f"kill-{uuid4()}", actor_id, status, note, datetime.now(timezone.utc)],
            )

    def list_kill_switch_events(self) -> list[dict]:
        try:
            with self.factory.connect(read_only=True) as conn:
                self._ensure_tables(conn)
                rows = conn.execute(
                    "SELECT event_id, actor_id, status, note, CAST(created_at AS VARCHAR) FROM kill_switch_events ORDER BY created_at DESC LIMIT 100"
                ).fetchall()
        except Exception:
            return []
        return [{"event_id": r[0], "actor_id": r[1], "status": r[2], "note": r[3], "created_at": r[4]} for r in rows]
