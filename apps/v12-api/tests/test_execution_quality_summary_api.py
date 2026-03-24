from fastapi.testclient import TestClient

from ai_hedge_bot.app.container import CONTAINER
from ai_hedge_bot.app.main import app
from ai_hedge_bot.api.routes import execution as execution_routes


client = TestClient(app)


def test_execution_quality_latest_summary_uses_latest_container_payload() -> None:
    execution_routes._execution_quality_summary_cache['expires_at'] = None
    execution_routes._execution_quality_summary_cache['payload'] = None
    original = dict(CONTAINER.latest_execution_quality)
    try:
        CONTAINER.latest_execution_quality = {
            "status": "ok",
            "snapshot_id": "snap-1",
            "created_at": "2026-03-24T00:00:00+00:00",
            "run_id": "run-1",
            "cycle_id": "cycle-1",
            "mode": "paper",
            "order_count": 5,
            "fill_count": 4,
            "fill_rate": 0.8,
            "avg_slippage_bps": 1.2,
            "latency_ms_p50": 35.0,
            "latency_ms_p95": 80.0,
            "latest_fills": [{"fill_id": "ignored"}],
            "latest_plans": [{"plan_id": "ignored"}],
        }
        response = client.get("/execution/quality/latest_summary")
        assert response.status_code == 200
        payload = response.json()
        assert payload["run_id"] == "run-1"
        assert payload["fill_rate"] == 0.8
        assert payload["fill_count"] == 4
        assert "latest_fills" not in payload
        assert "latest_plans" not in payload
    finally:
        CONTAINER.latest_execution_quality = original


def test_execution_quality_latest_summary_reuses_short_ttl_cache(monkeypatch) -> None:
    execution_routes._execution_quality_summary_cache['expires_at'] = None
    execution_routes._execution_quality_summary_cache['payload'] = None
    call_count = {'count': 0}

    def fake_summary() -> dict:
        call_count['count'] += 1
        return {
            'status': 'ok',
            'run_id': f'run-{call_count["count"]}',
            'fill_rate': 1.0,
            'fill_count': 1,
            'order_count': 1,
            'avg_slippage_bps': 0.0,
            'latency_ms_p50': 1.0,
            'latency_ms_p95': 1.0,
            'as_of': '2026-03-24T00:00:00+00:00',
        }

    monkeypatch.setattr(execution_routes._repo, 'latest_execution_quality_summary', fake_summary)

    first = client.get('/execution/quality/latest_summary')
    second = client.get('/execution/quality/latest_summary')

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json() == second.json()
    assert call_count['count'] == 1
