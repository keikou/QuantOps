from unittest.mock import AsyncMock

import pytest

from app.services.monitoring_service import MonitoringService


@pytest.mark.asyncio
async def test_worker_status_becomes_dead_on_stale_heartbeat() -> None:
    client = AsyncMock()
    client.get_system_health.return_value = {'status': 'ok', 'services': {}, 'as_of': '2026-03-18T00:00:00+00:00'}
    client.get_execution_quality.return_value = {'status': 'ok', 'latency_ms_p95': 10.0, 'as_of': '2026-03-18T00:00:00+00:00'}
    client.get_runtime_status.return_value = {'latest_run_id': 'r1', 'latest_run_timestamp': '2026-03-18T00:00:00+00:00', 'latest_execution_timestamp': '2026-03-18T00:00:00+00:00', 'as_of': '2026-03-18T00:00:00+00:00'}

    class Repo:
        factory = type('F', (), {'db_path': '/tmp/x.duckdb'})()
        def insert_snapshot(self, payload):
            return payload
        def latest_snapshot(self):
            return None

    service = MonitoringService(client, Repo())
    payload = await service.refresh()
    assert payload['worker_status'] == 'dead'
    assert payload['heartbeat_age_sec'] is not None
