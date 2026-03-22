CREATE TABLE IF NOT EXISTS monitoring_snapshots (
    snapshot_id TEXT PRIMARY KEY,
    system_status TEXT NOT NULL,
    execution_status TEXT NOT NULL,
    services_json TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS service_status_snapshots (
    snapshot_id TEXT PRIMARY KEY,
    service_name TEXT NOT NULL,
    service_status TEXT NOT NULL,
    detail_json TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL
);
