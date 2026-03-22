import json
import uuid
from app.clients.v12_client import utc_now_iso


class AlertRepository:

    def __init__(self, factory):
        self.factory = factory

    def _ensure_tables(self, conn):
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS alerts(
                alert_id VARCHAR PRIMARY KEY,
                alert_type VARCHAR,
                severity VARCHAR,
                source_service VARCHAR,
                source VARCHAR,
                title VARCHAR,
                message VARCHAR,
                status VARCHAR,
                payload_json VARCHAR,
                created_at TIMESTAMP,
                acknowledged_at TIMESTAMP,
                resolved_at TIMESTAMP
            )
            """
        )

    def create_alert(self, alert: dict) -> dict:

        with self.factory.connect() as conn:
            self._ensure_tables(conn)

            alert_id = alert.get("alert_id") or f"alert-{uuid.uuid4().hex[:12]}"
            payload_json = json.dumps(alert.get("payload", {}), ensure_ascii=False)

            now = utc_now_iso()

            conn.execute(
                """
                INSERT INTO alerts(
                    alert_id, alert_type, severity, source_service, source,
                    title, message, status, payload_json,
                    created_at, acknowledged_at, resolved_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    alert_id,
                    alert.get("alert_type"),
                    alert.get("severity"),
                    alert.get("source_service"),
                    alert.get("source"),
                    alert.get("title"),
                    alert.get("message"),
                    alert.get("status", "open"),
                    payload_json,
                    now,
                    None,
                    None,
                ],
            )

        return {
            "alert_id": alert_id,
            "status": "open",
        }

    def list_alerts(self) -> list[dict]:

        try:
            with self.factory.connect(read_only=True) as conn:

                try:
                    tables = {r[0] for r in conn.execute("SHOW TABLES").fetchall()}
                    if "alerts" not in tables:
                        return []
                except Exception:
                    row = conn.execute(
                        "SELECT name FROM sqlite_master WHERE type='table' AND name = ?",
                        ["alerts"],
                    ).fetchone()
                    if row is None:
                        return []

                rows = conn.execute(
                    """
                    SELECT
                        alert_id,
                        alert_type,
                        severity,
                        COALESCE(source, source_service),
                        title,
                        message,
                        status,
                        payload_json,
                        CAST(created_at AS VARCHAR),
                        CAST(acknowledged_at AS VARCHAR),
                        CAST(resolved_at AS VARCHAR)
                    FROM alerts
                    ORDER BY created_at DESC
                    """
                ).fetchall()

        except Exception:
            return []

        items = []

        for row in rows:

            payload = {}
            try:
                payload = json.loads(row[7] or "{}")
            except Exception:
                pass

            items.append(
                {
                    "alert_id": row[0],
                    "alert_type": row[1],
                    "severity": row[2],
                    "source": row[3],
                    "title": row[4],
                    "message": row[5],
                    "status": row[6],
                    "payload": payload,
                    "created_at": row[8],
                    "acknowledged_at": row[9],
                    "resolved_at": row[10],
                }
            )

        return items

    def find_open_by_type(self, alert_type: str) -> list[dict]:

        return [
            item
            for item in self.list_alerts()
            if item.get("alert_type") == alert_type and item.get("status") == "open"
        ]

    def acknowledge(self, alert_id: str, status: str = "acknowledged") -> dict:

        now = utc_now_iso()

        with self.factory.connect() as conn:

            self._ensure_tables(conn)

            conn.execute(
                """
                UPDATE alerts
                SET status = ?, acknowledged_at = COALESCE(acknowledged_at, ?)
                WHERE alert_id = ?
                """,
                [status, now, alert_id],
            )

        return {"alert_id": alert_id, "status": status}