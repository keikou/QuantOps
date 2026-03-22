from fastapi.testclient import TestClient

from app.main import app
from app.core.deps import get_risk_repository

client = TestClient(app)


def test_resume_and_run_blocked_for_execution_jobs_when_halted() -> None:
    repo = get_risk_repository()
    repo.set_trading_state("halted", "test")

    run_resp = client.post('/api/v1/scheduler/jobs/paper_cycle/run')
    assert run_resp.status_code == 200
    run_body = run_resp.json()
    assert run_body['ok'] is False
    assert run_body['blocked'] is True

    resume_resp = client.post('/api/v1/scheduler/jobs/paper_cycle/resume')
    assert resume_resp.status_code == 200
    resume_body = resume_resp.json()
    assert resume_body['ok'] is False
    assert resume_body['blocked'] is True
