from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app
from app.services.analytics_service import AnalyticsService
from app.services.execution_service import ExecutionService

client = TestClient(app)


def test_execution_summary_safe_fallback(monkeypatch) -> None:
    def boom(self):
        raise RuntimeError('summary unavailable')

    monkeypatch.setattr(AnalyticsService, 'execution_summary', boom)
    response = client.get('/api/v1/analytics/execution-summary')
    assert response.status_code == 200
    body = response.json()
    assert body['status'] == 'ok'
    assert body['degraded'] is True
    assert body['fill_rate'] == 0.0


def test_execution_orders_latest_state_limit() -> None:
    service = ExecutionService(v12_client=None)  # type: ignore[arg-type]
    rows = [
        {'order_id': 'o1', 'status': 'submitted', 'created_at': '2026-03-19T00:00:00+00:00'},
        {'order_id': 'o1', 'status': 'filled', 'created_at': '2026-03-19T00:01:00+00:00'},
        {'order_id': 'o2', 'status': 'submitted', 'created_at': '2026-03-19T00:02:00+00:00'},
    ]
    latest = service._latest_orders(rows, limit=10)
    assert len(latest) == 2
    by_id = {row['order_id']: row for row in latest}
    assert by_id['o1']['status'] == 'filled'


def test_execution_fills_limit() -> None:
    service = ExecutionService(v12_client=None)  # type: ignore[arg-type]
    rows = [
        {'fill_id': f'f{i}', 'created_at': f'2026-03-19T00:00:{i:02d}+00:00'} for i in range(5)
    ]
    latest = service._latest_fills(rows, limit=3)
    assert len(latest) == 3
    assert latest[0]['fill_id'] == 'f4'
