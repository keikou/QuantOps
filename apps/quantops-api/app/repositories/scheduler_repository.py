from app.core.trading_state import derive_effective_job_status, is_execution_job

class SchedulerRepository:

    def __init__(self, factory):
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

    def _ensure_tables(self, conn):

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS scheduler_jobs(
                job_id VARCHAR PRIMARY KEY,
                job_name VARCHAR,
                job_group VARCHAR,
                cadence_type VARCHAR,
                cadence_value VARCHAR,
                enabled BOOLEAN,
                allow_manual_run BOOLEAN,
                owner_service VARCHAR,
                updated_at TIMESTAMP
            )
            """
        )

    def list_jobs(self, trading_state: str = "running") -> list[dict]:

        try:
            with self.factory.connect(read_only=True) as conn:

                if not self._table_exists(conn, "scheduler_jobs"):
                    return []

                rows = conn.execute(
                    """
                    SELECT
                        job_id,
                        job_name,
                        job_group,
                        cadence_type,
                        cadence_value,
                        enabled,
                        allow_manual_run,
                        owner_service,
                        CAST(updated_at AS VARCHAR)
                    FROM scheduler_jobs
                    ORDER BY job_group, job_name
                    """
                ).fetchall()

        except Exception:
            return []

        jobs = []

        for r in rows:
            jobs.append(
                {
                    "job_id": r[0],
                    "job_name": r[1],
                    "job_group": r[2],
                    "cadence_type": r[3],
                    "cadence_value": r[4],
                    "enabled": bool(r[5]),
                    "allow_manual_run": bool(r[6]),
                    "owner_service": r[7],
                    "updated_at": r[8],
                    "status": derive_effective_job_status(bool(r[5]), trading_state, is_execution_job(job_id=r[0], job_name=r[1], job_group=r[2])),
                    "execution_blocked": bool(is_execution_job(job_id=r[0], job_name=r[1], job_group=r[2]) and str(trading_state or "running").lower() in {"halted", "paused"}),
                }
            )

        return jobs