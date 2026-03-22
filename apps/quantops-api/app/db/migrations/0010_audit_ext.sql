CREATE TABLE IF NOT EXISTS config_change_logs (
    change_id TEXT PRIMARY KEY,
    actor_id TEXT NOT NULL,
    config_scope TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS mode_switch_logs (
    switch_id TEXT PRIMARY KEY,
    actor_id TEXT NOT NULL,
    from_mode TEXT NOT NULL,
    to_mode TEXT NOT NULL,
    note TEXT,
    created_at TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS kill_switch_events (
    event_id TEXT PRIMARY KEY,
    actor_id TEXT NOT NULL,
    status TEXT NOT NULL,
    note TEXT,
    created_at TIMESTAMP NOT NULL
);
