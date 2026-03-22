from __future__ import annotations

import os

from fastapi.testclient import TestClient

DB_PATH = "/tmp/quantops_sprint3_integrated.duckdb"
os.environ["QUANTOPS_DB_PATH"] = DB_PATH
os.environ.setdefault("V12_MOCK_MODE", "true")

from app.db.migrate import main as migrate_main
migrate_main()
from app.main import app

client = TestClient(app)


def test_monitoring_and_governance_refresh() -> None:
    r = client.post("/api/v1/monitoring/refresh")
    assert r.status_code == 200
    g = client.post("/api/v1/governance/refresh")
    assert g.status_code == 200
    sys = client.get("/api/v1/monitoring/system")
    assert sys.status_code == 200
    assert sys.json()["status"] == "ok"


def test_approval_incident_admin_flow() -> None:
    req = client.post("/api/v1/approval/request", json={"request_type": "promotion", "target_id": "s1", "requested_by": "operator", "summary": {"reason": "pytest"}})
    assert req.status_code == 200
    request_id = req.json()["request_id"]
    appv = client.post("/api/v1/approval/approve", json={"request_id": request_id, "actor_id": "tester", "note": "ok"})
    assert appv.status_code == 200
    inc = client.post("/api/v1/incidents/create", json={"incident_type": "service_unhealthy", "severity": "medium", "title": "pytest incident", "description": "created by test"})
    assert inc.status_code == 200
    audit = client.get("/api/v1/admin/audit-logs")
    assert audit.status_code == 200
    assert isinstance(audit.json()["items"], list)
