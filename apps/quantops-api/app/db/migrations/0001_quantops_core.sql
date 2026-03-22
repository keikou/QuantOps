CREATE TABLE IF NOT EXISTS schema_migrations (
    version TEXT PRIMARY KEY,
    applied_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS operator_actions (
    action_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    role_name TEXT NOT NULL,
    action_type TEXT NOT NULL,
    target_type TEXT NOT NULL,
    target_id TEXT NOT NULL,
    request_json TEXT,
    result_status TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS audit_logs (
    log_id TEXT PRIMARY KEY,
    category TEXT NOT NULL,
    actor_id TEXT,
    actor_role TEXT,
    event_type TEXT NOT NULL,
    ref_type TEXT,
    ref_id TEXT,
    payload_json TEXT,
    created_at TIMESTAMP NOT NULL
);
