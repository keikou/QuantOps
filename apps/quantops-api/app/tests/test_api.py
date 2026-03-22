from __future__ import annotations

import os
from pathlib import Path

from fastapi.testclient import TestClient

DB_PATH = "/tmp/quantops_sprint2_pytest.duckdb"
os.environ["QUANTOPS_DB_PATH"] = DB_PATH
os.environ.setdefault("V12_MOCK_MODE", "true")

from app.db.migrate import main as migrate_main
migrate_main()
from app.main import app

client = TestClient(app)


def test_health() -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_dashboard_overview() -> None:
    response = client.get("/api/v1/dashboard/overview")
    assert response.status_code == 200
    body = response.json()
    assert "portfolio_value" in body
    assert "gross_exposure" in body


def test_analytics_refresh_and_alpha() -> None:
    refresh = client.post("/api/v1/analytics/refresh")
    assert refresh.status_code == 200
    assert refresh.json()["ok"] is True

    alpha = client.get("/api/v1/analytics/alpha")
    assert alpha.status_code == 200
    body = alpha.json()
    assert body["count"] >= 1
    assert len(body["items"]) >= 1


def test_control_runtime_state() -> None:
    response = client.post("/api/v1/control/pause-strategy", json={"strategy_id": "s1"})
    assert response.status_code == 200
    state = client.get("/api/v1/analytics/runtime-states")
    assert state.status_code == 200
    rows = state.json()
    assert any(row["strategy_id"] == "s1" and row["desired_state"] == "paused" for row in rows)
