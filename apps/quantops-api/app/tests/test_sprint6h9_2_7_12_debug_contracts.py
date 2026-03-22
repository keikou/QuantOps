from __future__ import annotations

import os
from pathlib import Path
from tempfile import gettempdir

from fastapi.testclient import TestClient

DB_PATH = Path(gettempdir()) / "quantops_sprint6h9_2_7_12_debug_contracts.sqlite3"
if DB_PATH.exists():
    DB_PATH.unlink()

os.environ["QUANTOPS_DB_PATH"] = str(DB_PATH)
os.environ.setdefault("V12_MOCK_MODE", "true")

from app.db.migrate import main as migrate_main

migrate_main()

from app.main import app

client = TestClient(app)


def _assert_debug_envelope(payload: dict, scope: str) -> None:
    assert payload["scope"] == scope
    assert payload["status"] in {"ok", "stale", "no_data"}
    assert payload["source"] in {"live", "cache", "empty"}
    assert "reason" in payload
    assert "as_of" in payload
    assert isinstance(payload.get("timings"), dict)
    assert isinstance(payload.get("summary"), dict)
    assert isinstance(payload.get("provenance"), dict)
    assert isinstance(payload.get("counts"), dict)
    assert isinstance(payload.get("raw"), dict)


def test_debug_routes_return_stable_contract_envelopes() -> None:
    client.post("/api/v1/risk/refresh")
    client.post("/api/v1/monitoring/refresh")

    route_scopes = {
        "/api/v1/risk/debug/snapshot": "risk.snapshot",
        "/api/v1/monitoring/debug/system": "monitoring.system",
        "/api/v1/command-center/debug/execution": "command_center.execution",
        "/api/v1/dashboard/debug/overview": "dashboard.overview",
        "/api/v1/portfolio/debug/overview": "portfolio.overview",
        "/api/v1/portfolio/debug/positions": "portfolio.positions",
    }

    for route, scope in route_scopes.items():
        response = client.get(route)
        assert response.status_code == 200, route
        _assert_debug_envelope(response.json(), scope)
