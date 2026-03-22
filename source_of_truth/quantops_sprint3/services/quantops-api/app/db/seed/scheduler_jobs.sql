INSERT OR IGNORE INTO scheduler_jobs(
    job_id, job_name, job_group, cadence_type, cadence_value,
    enabled, allow_manual_run, owner_service, updated_at
) VALUES
('job-signal-cycle', 'signal_cycle', 'runtime', 'interval', '60s', TRUE, TRUE, 'quantops-scheduler', NOW()),
('job-portfolio-rebalance', 'portfolio_rebalance', 'runtime', 'interval', '300s', TRUE, TRUE, 'quantops-scheduler', NOW()),
('job-risk-snapshot', 'risk_snapshot', 'monitoring', 'interval', '60s', TRUE, TRUE, 'quantops-scheduler', NOW()),
('job-analytics-refresh', 'analytics_refresh', 'analytics', 'interval', '900s', TRUE, TRUE, 'quantops-scheduler', NOW());
