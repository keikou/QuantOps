CREATE TABLE IF NOT EXISTS runtime_runs (
    run_id VARCHAR PRIMARY KEY,
    job_name VARCHAR NOT NULL,
    mode VARCHAR NOT NULL,
    started_at TIMESTAMP NOT NULL,
    finished_at TIMESTAMP,
    status VARCHAR NOT NULL,
    error_message VARCHAR,
    duration_ms BIGINT,
    triggered_by VARCHAR,
    created_at TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS runtime_run_steps (
    step_id VARCHAR PRIMARY KEY,
    run_id VARCHAR NOT NULL,
    step_name VARCHAR NOT NULL,
    status VARCHAR NOT NULL,
    started_at TIMESTAMP NOT NULL,
    finished_at TIMESTAMP,
    duration_ms BIGINT,
    error_message VARCHAR,
    payload_json VARCHAR
);

CREATE TABLE IF NOT EXISTS scheduler_jobs (
    job_id VARCHAR PRIMARY KEY,
    job_name VARCHAR NOT NULL,
    cadence VARCHAR,
    enabled BOOLEAN NOT NULL,
    owner_service VARCHAR,
    mode VARCHAR,
    updated_at TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS scheduler_runs (
    scheduler_run_id VARCHAR PRIMARY KEY,
    job_id VARCHAR NOT NULL,
    run_id VARCHAR,
    trigger_type VARCHAR NOT NULL,
    status VARCHAR NOT NULL,
    started_at TIMESTAMP NOT NULL,
    finished_at TIMESTAMP,
    duration_ms BIGINT,
    error_message VARCHAR
);

CREATE TABLE IF NOT EXISTS runtime_checkpoints (
    checkpoint_id VARCHAR PRIMARY KEY,
    run_id VARCHAR NOT NULL,
    checkpoint_name VARCHAR NOT NULL,
    created_at TIMESTAMP NOT NULL,
    payload_json VARCHAR
);

CREATE TABLE IF NOT EXISTS audit_logs (
    audit_id VARCHAR PRIMARY KEY,
    category VARCHAR NOT NULL,
    event_type VARCHAR NOT NULL,
    run_id VARCHAR,
    created_at TIMESTAMP NOT NULL,
    payload_json VARCHAR,
    actor VARCHAR
);
