from unittest.mock import AsyncMock

import pytest

from app.services.monitoring_service import MonitoringService


@pytest.mark.asyncio
async def test_sprint6h9_monitoring_refresh_exposes_execution_truth_fields() -> None:
    client = AsyncMock()
    client.get_system_health.return_value = {'status': 'ok', 'services': {}, 'as_of': '2026-03-20T00:00:00+00:00'}
    client.get_execution_quality.return_value = {'status': 'ok', 'latency_ms_p95': 12.0, 'as_of': '2026-03-20T00:00:05+00:00'}
    client.get_runtime_status.return_value = {'latest_run_id': 'r1', 'latest_run_timestamp': '2026-03-20T00:00:05+00:00', 'latest_execution_timestamp': '2026-03-20T00:00:05+00:00', 'as_of': '2026-03-20T00:00:05+00:00'}
    client.get_execution_planner_latest.return_value = {'status': 'ok', 'plan_count': 1, 'as_of': '2026-03-20T00:00:05+00:00'}
    client.get_execution_state_latest.return_value = {
        'status': 'ok',
        'execution_state': 'degraded',
        'reason': 'planner_no_execution',
        'block_reasons': [{'code': 'planner_no_execution'}],
        'as_of': '2026-03-20T00:00:05+00:00',
    }
    client.get_execution_block_reasons_latest.return_value = {'status': 'ok', 'items': [{'code': 'planner_no_execution'}], 'as_of': '2026-03-20T00:00:05+00:00'}

    class Repo:
        factory = type('F', (), {'db_path': '/tmp/x.duckdb'})()
        def insert_snapshot(self, payload):
            return payload
        def latest_snapshot(self):
            return None

    service = MonitoringService(client, Repo())
    payload = await service.refresh()
    assert payload['execution_state_name'] == 'degraded'
    assert payload['execution_reason'] == 'planner_no_execution'

    system = await service.get_system()
    assert system['executionState'] == 'degraded'
    assert system['executionReason'] == 'planner_no_execution'
