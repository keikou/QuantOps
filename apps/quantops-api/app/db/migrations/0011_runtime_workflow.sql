CREATE TABLE IF NOT EXISTS runtime_run_reviews(
    run_id VARCHAR PRIMARY KEY,
    review_status VARCHAR,
    acknowledged BOOLEAN,
    operator_note VARCHAR,
    reviewed_by VARCHAR,
    reviewed_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS runtime_issue_acknowledgements(
    diagnosis_code VARCHAR PRIMARY KEY,
    note VARCHAR,
    acknowledged_by VARCHAR,
    acknowledged_at TIMESTAMP
);
