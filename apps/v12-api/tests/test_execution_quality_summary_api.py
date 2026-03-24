from fastapi.testclient import TestClient

from ai_hedge_bot.app.container import CONTAINER
from ai_hedge_bot.app.main import app


client = TestClient(app)


def test_execution_quality_latest_summary_uses_latest_container_payload() -> None:
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
