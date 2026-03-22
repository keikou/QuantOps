CREATE TABLE IF NOT EXISTS scheduler_jobs (
    job_id TEXT PRIMARY KEY,
    job_name TEXT NOT NULL UNIQUE,
    job_group TEXT NOT NULL,
    cadence_type TEXT NOT NULL,
    cadence_value TEXT NOT NULL,
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    allow_manual_run BOOLEAN NOT NULL DEFAULT TRUE,
    last_run_at TIMESTAMP,
    next_run_at TIMESTAMP,
    owner_service TEXT NOT NULL,
    updated_at TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS scheduler_runs (
    run_id TEXT PRIMARY KEY,
    job_id TEXT NOT NULL,
    trigger_type TEXT NOT NULL,
    run_status TEXT NOT NULL,
    requested_by TEXT,
    started_at TIMESTAMP NOT NULL,
    finished_at TIMESTAMP,
    duration_ms BIGINT,
    result_json TEXT,
    error_message TEXT
);
