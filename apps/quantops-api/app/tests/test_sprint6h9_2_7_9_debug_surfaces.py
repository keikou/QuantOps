from __future__ import annotations

import os
from pathlib import Path
from tempfile import gettempdir

from fastapi.testclient import TestClient

DB_PATH = Path(gettempdir()) / 'quantops_sprint6h9_2_7_9_debug.sqlite3'
if DB_PATH.exists():
    DB_PATH.unlink()
os.environ['QUANTOPS_DB_PATH'] = str(DB_PATH)
os.environ.setdefault('V12_MOCK_MODE', 'true')

from app.db.migrate import main as migrate_main
migrate_main()
from app.main import app

client = TestClient(app)


def test_risk_debug_snapshot_returns_status_provenance_and_raw_payload() -> None:
    refresh = client.post('/api/v1/risk/refresh')
    assert refresh.status_code == 200

    response = client.get('/api/v1/risk/debug/snapshot')
    assert response.status_code == 200
    body = response.json()

    assert body['scope'] == 'risk.snapshot'
    assert body['status'] in {'ok', 'stale', 'no_data'}
    assert body['source'] in {'cache', 'empty'}
    assert 'timings' in body
    assert 'summary' in body
    assert body['provenance']['snapshot_store'] == 'risk_snapshots'
    assert 'v12:/portfolio/positions/latest' in body['provenance']['upstream_dependencies']
    assert 'snapshot' in body['raw']


def test_monitoring_debug_system_returns_status_provenance_and_service_counts() -> None:
    refresh = client.post('/api/v1/monitoring/refresh')
    assert refresh.status_code == 200

    response = client.get('/api/v1/monitoring/debug/system')
    assert response.status_code == 200
    body = response.json()

    assert body['scope'] == 'monitoring.system'
    assert body['status'] in {'ok', 'stale', 'no_data'}
    assert body['source'] in {'cache', 'empty'}
    assert 'timings' in body
    assert 'summary' in body
    assert body['provenance']['snapshot_store'] == 'monitoring_snapshots'
    assert 'v12:/execution/state/latest' in body['provenance']['upstream_dependencies']
    assert 'services' in body['raw']
