from fastapi.testclient import TestClient

from app.main import app
from app.core.deps import get_risk_repository

client = TestClient(app)


def test_run_now_blocked_when_halted() -> None:
    repo = get_risk_repository()
    repo.set_trading_state("halted", "test")
    response = client.post('/api/v1/scheduler/run-now')
    assert response.status_code == 200
    payload = response.json()
    assert payload['ok'] is False
    assert payload['blocked'] is True
    assert payload['run_status'] == 'halted'


def test_scheduler_jobs_endpoint_survives_halt() -> None:
    repo = get_risk_repository()
    repo.set_trading_state("halted", "test")
    response = client.get('/api/v1/scheduler/jobs')
    assert response.status_code == 200
    payload = response.json()
    assert isinstance(payload, dict)
