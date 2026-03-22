from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4
import json

from app.repositories.duckdb import DuckDBConnectionFactory


class MonitoringRepository:
    def __init__(self, factory: DuckDBConnectionFactory) -> None:
        self.factory = factory

    def _table_columns(self, conn, table_name: str) -> set[str]:
        try:
            tables = {row[0] for row in conn.execute("SHOW TABLES").fetchall()}
            if table_name not in tables:
                return set()
        except Exception:
            row = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name = ?",
                [table_name],
            ).fetchone()
            if row is None:
                return set()
        return {row[1] for row in conn.execute(f"PRAGMA table_info('{table_name}')").fetchall()}

    def _ensure_tables(self, conn) -> None:
        columns = self._table_columns(conn, 'monitoring_snapshots')
        expected = {
            'snapshot_id','system_status','execution_status','services_json','payload_json','cpu','memory','disk',
            'db_writable','exchange_latency_ms','data_freshness_sec','exchange','latency_ms','queue','worker_status','created_at'
        }
        if columns and columns != expected:
            conn.execute('DROP TABLE IF EXISTS monitoring_snapshots')
            conn.execute('DROP TABLE IF EXISTS service_status_snapshots')
            columns = set()
        if not columns:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS monitoring_snapshots(
                    snapshot_id VARCHAR PRIMARY KEY,
                    system_status VARCHAR,
                    execution_status VARCHAR,
                    services_json VARCHAR,
                    payload_json VARCHAR,
                    cpu DOUBLE,
                    memory DOUBLE,
                    disk VARCHAR,
                    db_writable BOOLEAN,
                    exchange_latency_ms DOUBLE,
                    data_freshness_sec DOUBLE,
                    exchange VARCHAR,
                    latency_ms DOUBLE,
                    queue INTEGER,
                    worker_status VARCHAR,
                    created_at TIMESTAMP
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS service_status_snapshots(
                    snapshot_id VARCHAR PRIMARY KEY,
                    service_name VARCHAR,
                    service_status VARCHAR,
                    detail_json VARCHAR,
                    created_at TIMESTAMP
                )
                """
            )

    def insert_snapshot(self, payload: dict) -> dict:
        now = datetime.now(timezone.utc)
        snapshot_id = f"mon-{uuid4()}"
        with self.factory.connect() as conn:
            self._ensure_tables(conn)
            conn.execute(
                """INSERT INTO monitoring_snapshots(snapshot_id, system_status, execution_status, services_json, payload_json, cpu, memory, disk, db_writable, exchange_latency_ms, data_freshness_sec, exchange, latency_ms, queue, worker_status, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                [snapshot_id, payload.get('system_status'), payload.get('execution_status'), json.dumps(payload.get('services', {})), json.dumps(payload), float(payload.get('cpu', 0.0) or 0.0), float(payload.get('memory', 0.0) or 0.0), str(payload.get('disk', 'unknown')), bool(payload.get('db_writable', False)), float(payload.get('exchange_latency_ms', 0.0) or 0.0), float(payload.get('data_freshness_sec', 0.0) or 0.0), str(payload.get('exchange', '')), float(payload.get('latency_ms', 0.0) or 0.0), int(payload.get('queue', 0) or 0), str(payload.get('worker_status', 'unknown')), now],
            )
            for service_name, detail in (payload.get('services') or {}).items():
                conn.execute(
                    """INSERT INTO service_status_snapshots(snapshot_id, service_name, service_status, detail_json, created_at) VALUES (?, ?, ?, ?, ?)""",
                    [f"svc-{uuid4()}", service_name, str(detail), json.dumps({'status': detail}), now],
                )
        payload['as_of'] = now.isoformat()
        return payload

    def latest_snapshot(self) -> dict | None:
        try:
            with self.factory.connect(read_only=True) as conn:
                self._ensure_tables(conn)
                row = conn.execute("SELECT payload_json, CAST(created_at AS VARCHAR) FROM monitoring_snapshots ORDER BY created_at DESC LIMIT 1").fetchone()
        except Exception:
            return None
        if row is None:
            return None
        payload = json.loads(row[0])
        payload['as_of'] = row[1]
        return payload

    def latest_service_statuses(self) -> list[dict]:
        try:
            with self.factory.connect(read_only=True) as conn:
                self._ensure_tables(conn)
                rows = conn.execute(
                    """SELECT service_name, service_status, detail_json, CAST(created_at AS VARCHAR) FROM service_status_snapshots ORDER BY created_at DESC LIMIT 20"""
                ).fetchall()
        except Exception:
            return []
        return [{'service_name': r[0], 'service_status': r[1], 'detail': json.loads(r[2]), 'as_of': r[3]} for r in rows]
