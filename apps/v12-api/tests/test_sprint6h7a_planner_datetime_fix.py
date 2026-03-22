from datetime import datetime, timezone

from fastapi.testclient import TestClient

from ai_hedge_bot.app.main import app
from ai_hedge_bot.api.routes.execution import _plan_status
from ai_hedge_bot.app.container import CONTAINER

client = TestClient(app)


def _reset() -> None:
    for table in ["execution_plans", "market_prices_latest", "runtime_control_state"]:
        try:
            CONTAINER.runtime_store.execute(f"DELETE FROM {table}")
        except Exception:
            pass


def test_plan_status_accepts_naive_datetime() -> None:
    status = _plan_status({"created_at": datetime.utcnow(), "status": "planned"})
    assert status == "planned"


def test_plan_status_accepts_aware_datetime() -> None:
    status = _plan_status({"created_at": datetime.now(timezone.utc), "status": "planned"})
    assert status == "planned"


def test_execution_planner_latest_handles_naive_created_at() -> None:
    _reset()
    CONTAINER.runtime_store.execute(
        """
        INSERT INTO execution_plans (
            plan_id, created_at, run_id, mode, symbol, side, target_weight, order_qty,
            limit_price, participation_rate, status, algo, route, expire_seconds, slice_count, metadata_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            "plan_test_naive",
            datetime.utcnow().isoformat(),
            "run_test",
            "paper",
            "BTCUSDT",
            "buy",
            0.1,
            1.0,
            100.0,
            0.1,
            "planned",
            "twap",
            "paper",
            60,
            2,
            '{\"expire_seconds\": 60}',
        ],
    )
    res = client.get('/execution/planner/latest')
    assert res.status_code == 200
    body = res.json()
    assert body['status'] == 'ok'
    assert isinstance(body['items'], list)
