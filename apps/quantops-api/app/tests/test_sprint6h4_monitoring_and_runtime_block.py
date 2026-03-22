from app.services.monitoring_service import MonitoringService


def test_sprint6h4_worker_activity_prefers_execution_timestamp() -> None:
    service = MonitoringService.__new__(MonitoringService)
    status, last_as_of, age = service._worker_activity(
        {'latest_run_timestamp': '2026-03-19T00:00:09+00:00', 'latest_execution_timestamp': None, 'as_of': '2026-03-19T00:00:09+00:00'},
        {'as_of': None},
        {'as_of': '2026-03-19T00:00:09+00:00'},
    )
    assert status == 'idle'
    assert last_as_of is not None
    assert age is not None
