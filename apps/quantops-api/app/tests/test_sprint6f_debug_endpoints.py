from __future__ import annotations

import os

from fastapi.testclient import TestClient

DB_PATH = '/tmp/quantops_sprint6f_debug.duckdb'
os.environ['QUANTOPS_DB_PATH'] = DB_PATH
os.environ.setdefault('V12_MOCK_MODE', 'true')

from app.db.migrate import main as migrate_main
migrate_main()
from app.main import app

client = TestClient(app)


def test_sprint6f_execution_endpoints() -> None:
    refresh = client.post('/api/v1/analytics/refresh')
    assert refresh.status_code == 200

    summary = client.get('/api/v1/analytics/execution-summary')
    assert summary.status_code == 200
    assert 'fill_rate' in summary.json()

    latest = client.get('/api/v1/analytics/execution-latest')
    assert latest.status_code == 200
    assert 'items' in latest.json()


def test_sprint6f_monitoring_and_alerts() -> None:
    monitoring = client.get('/api/v1/monitoring/system')
    assert monitoring.status_code == 200
    body = monitoring.json()
    assert 'cpu' in body
    assert 'exchange_latency_ms' in body

    risk = client.post('/api/v1/risk/refresh')
    assert risk.status_code == 200

    alerts = client.get('/api/v1/alerts')
    assert alerts.status_code == 200
    assert 'items' in alerts.json()
