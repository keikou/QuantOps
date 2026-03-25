from __future__ import annotations

from datetime import datetime, timezone

from app.repositories.duckdb import DuckDBConnectionFactory


class RuntimeWorkflowRepository:
    def __init__(self, factory: DuckDBConnectionFactory) -> None:
        self.factory = factory

    def _ensure_tables(self, conn) -> None:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS runtime_run_reviews(
                run_id VARCHAR PRIMARY KEY,
                review_status VARCHAR,
                acknowledged BOOLEAN,
                operator_note VARCHAR,
                reviewed_by VARCHAR,
                reviewed_at TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS runtime_issue_acknowledgements(
                diagnosis_code VARCHAR PRIMARY KEY,
                note VARCHAR,
                acknowledged_by VARCHAR,
                acknowledged_at TIMESTAMP
            )
            """
        )

    def upsert_run_review(
        self,
        *,
        run_id: str,
        review_status: str,
        acknowledged: bool,
        operator_note: str,
        reviewed_by: str,
    ) -> dict:
        reviewed_at = datetime.now(timezone.utc)
        with self.factory.connect() as conn:
            self._ensure_tables(conn)
            conn.execute(
                """
                INSERT INTO runtime_run_reviews(
                    run_id, review_status, acknowledged, operator_note, reviewed_by, reviewed_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT (run_id) DO UPDATE SET
                    review_status = excluded.review_status,
                    acknowledged = excluded.acknowledged,
                    operator_note = excluded.operator_note,
                    reviewed_by = excluded.reviewed_by,
                    reviewed_at = excluded.reviewed_at
                """,
                [run_id, review_status, acknowledged, operator_note, reviewed_by, reviewed_at],
            )
        return {
            "run_id": run_id,
            "review_status": review_status,
            "acknowledged": acknowledged,
            "operator_note": operator_note,
            "reviewed_by": reviewed_by,
            "reviewed_at": reviewed_at.isoformat(),
        }

    def acknowledge_issue(
        self,
        *,
        diagnosis_code: str,
        note: str,
        acknowledged_by: str,
    ) -> dict:
        acknowledged_at = datetime.now(timezone.utc)
        with self.factory.connect() as conn:
            self._ensure_tables(conn)
            conn.execute(
                """
                INSERT INTO runtime_issue_acknowledgements(
                    diagnosis_code, note, acknowledged_by, acknowledged_at
                ) VALUES (?, ?, ?, ?)
                ON CONFLICT (diagnosis_code) DO UPDATE SET
                    note = excluded.note,
                    acknowledged_by = excluded.acknowledged_by,
                    acknowledged_at = excluded.acknowledged_at
                """,
                [diagnosis_code, note, acknowledged_by, acknowledged_at],
            )
        return {
            "diagnosis_code": diagnosis_code,
            "note": note,
            "acknowledged_by": acknowledged_by,
            "acknowledged_at": acknowledged_at.isoformat(),
        }

    def get_run_reviews(self, run_ids: list[str]) -> dict[str, dict]:
        normalized = [str(run_id) for run_id in run_ids if str(run_id)]
        if not normalized:
            return {}
        placeholders = ",".join(["?"] * len(normalized))
        try:
            with self.factory.connect(read_only=True) as conn:
                rows = conn.execute(
                    f"""
                    SELECT run_id, review_status, acknowledged, operator_note, reviewed_by, CAST(reviewed_at AS VARCHAR)
                    FROM runtime_run_reviews
                    WHERE run_id IN ({placeholders})
                    """,
                    normalized,
                ).fetchall()
        except Exception:
            return {}
        return {
            str(row[0]): {
                "run_id": str(row[0]),
                "review_status": str(row[1] or "new"),
                "acknowledged": bool(row[2]),
                "operator_note": str(row[3] or ""),
                "reviewed_by": str(row[4] or ""),
                "reviewed_at": str(row[5] or ""),
            }
            for row in rows
        }

    def get_issue_acknowledgements(self, diagnosis_codes: list[str]) -> dict[str, dict]:
        normalized = [str(code) for code in diagnosis_codes if str(code)]
        if not normalized:
            return {}
        placeholders = ",".join(["?"] * len(normalized))
        try:
            with self.factory.connect(read_only=True) as conn:
                rows = conn.execute(
                    f"""
                    SELECT diagnosis_code, note, acknowledged_by, CAST(acknowledged_at AS VARCHAR)
                    FROM runtime_issue_acknowledgements
                    WHERE diagnosis_code IN ({placeholders})
                    """,
                    normalized,
                ).fetchall()
        except Exception:
            return {}
        return {
            str(row[0]): {
                "diagnosis_code": str(row[0]),
                "note": str(row[1] or ""),
                "acknowledged_by": str(row[2] or ""),
                "acknowledged_at": str(row[3] or ""),
            }
            for row in rows
        }
