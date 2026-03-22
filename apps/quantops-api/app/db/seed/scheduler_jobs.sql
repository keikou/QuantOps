INSERT OR IGNORE INTO scheduler_jobs(
    job_id,
    job_name,
    job_group,
    cadence_type,
    cadence_value,
    enabled,
    allow_manual_run,
    owner_service,
    updated_at
)
VALUES
('job-signal-cycle','signal_cycle','strategy','manual','manual',TRUE,TRUE,'quantops-scheduler',NOW()),
('job-portfolio-rebalance','portfolio_rebalance','portfolio','manual','manual',TRUE,TRUE,'quantops-scheduler',NOW()),
('job-risk-snapshot','risk_snapshot','risk','interval','5s',TRUE,TRUE,'quantops-scheduler',NOW()),
('job-analytics-refresh','analytics_refresh','analytics','interval','15s',TRUE,TRUE,'quantops-scheduler',NOW()),
('job-alert-evaluator','alert_evaluator','monitoring','interval','10s',TRUE,TRUE,'quantops-scheduler',NOW());