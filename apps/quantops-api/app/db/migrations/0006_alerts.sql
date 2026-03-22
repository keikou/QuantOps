CREATE TABLE IF NOT EXISTS alert_events (
    event_id TEXT PRIMARY KEY,
    alert_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    actor_id TEXT,
    note TEXT,
    created_at TIMESTAMP NOT NULL
);

ALTER TABLE alerts ADD COLUMN IF NOT EXISTS payload_json TEXT;
ALTER TABLE alerts ADD COLUMN IF NOT EXISTS acknowledged_at TIMESTAMP;
ALTER TABLE alerts ADD COLUMN IF NOT EXISTS source TEXT;
