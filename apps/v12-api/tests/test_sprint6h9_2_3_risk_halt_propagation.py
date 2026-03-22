from datetime import datetime, timezone

from fastapi.testclient import TestClient

from ai_hedge_bot.app.main import app
from ai_hedge_bot.app.container import CONTAINER

client = TestClient(app)


def _reset_runtime_state() -> None:
    for table in [
        "runtime_control_state","execution_plans","execution_fills","execution_orders","execution_quality_snapshots",
        "execution_state_snapshots","execution_block_reasons"
    ]:
        try:
            CONTAINER.runtime_store.execute(f"DELETE FROM {table}")
        except Exception:
            pass


def test_sprint6h9_2_3_execution_state_keeps_residual_orders_visible_after_halt() -> None:
    _reset_runtime_state()
    now = datetime.now(timezone.utc).isoformat()
    CONTAINER.runtime_store.execute("INSERT INTO runtime_control_state (state_id, trading_state, note, created_at) VALUES (?, ?, ?, ?)", ["state-halt-1", "halted", "test", now])
    CONTAINER.runtime_store.append("execution_plans", {
        "plan_id": "plan-halt-1", "created_at": now, "run_id": "run-1", "mode": "paper", "symbol": "BTCUSDT", "side": "buy",
        "target_weight": 0.1, "order_qty": 1.0, "limit_price": 100.0, "participation_rate": 0.1, "status": "planned",
        "algo": "twap", "route": "primary", "expire_seconds": 120, "slice_count": 1, "metadata_json": "{}"
    })
    CONTAINER.runtime_store.append("execution_orders", {
        "order_id": "order-halt-1", "plan_id": "plan-halt-1", "parent_order_id": None, "client_order_id": "client-halt-1",
        "strategy_id": "s1", "alpha_family": "trend", "symbol": "BTCUSDT", "side": "buy", "order_type": "limit", "qty": 1.0,
        "limit_price": 100.0, "venue": "paper", "route": "primary", "algo": "twap", "submit_time": now,
        "status": "submitted", "source": "planner", "metadata_json": "{}", "created_at": now, "updated_at": now
    })

    state = client.get('/execution/state/latest').json()
    assert state['trading_state'] == 'halted'
    assert state['execution_state'] == 'halted'
    assert state['open_order_count'] >= 1
    assert state['reason'] in {'risk_halted', 'residual_orders_after_halt', 'kill_switch_triggered'}
