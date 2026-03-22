from unittest.mock import AsyncMock

import pytest

from app.services.monitoring_service import MonitoringService


@pytest.mark.asyncio
async def test_sprint6h9_2_3_monitoring_exposes_risk_halt_truth() -> None:
    client = AsyncMock()
    client.get_system_health.return_value = {"status": "ok", "services": {}, "as_of": "2026-03-20T00:00:00+00:00"}
    client.get_execution_quality.return_value = {"status": "ok", "latency_ms_p95": 12.0, "as_of": "2026-03-20T00:00:05+00:00"}
    client.get_runtime_status.return_value = {"latest_run_id": "r1", "latest_run_timestamp": "2026-03-20T00:00:05+00:00", "latest_execution_timestamp": "2026-03-20T00:00:05+00:00", "as_of": "2026-03-20T00:00:05+00:00"}
    client.get_execution_planner_latest.return_value = {"status": "ok", "plan_count": 0, "latest_activity_at": "2026-03-20T00:00:05+00:00", "as_of": "2026-03-20T00:00:05+00:00"}
    client.get_execution_state_latest.return_value = {"status": "ok", "execution_state": "halted", "reason": "risk_halted", "open_order_count": 12, "block_reasons": [{"code": "risk_halted"}], "as_of": "2026-03-20T00:00:05+00:00"}
    client.get_execution_block_reasons_latest.return_value = {"status": "ok", "items": [{"code": "risk_halted"}], "as_of": "2026-03-20T00:00:05+00:00"}
    client.get_risk_budget.return_value = {"status": "ok"}
    client.get_sprint5c_risk_latest.return_value = {"trading_state": "halted", "kill_switch": "triggered", "alert_state": "breach"}

    class Repo:
        factory = type("F", (), {"db_path": "/tmp/x.duckdb"})()
        def insert_snapshot(self, payload):
            return payload
        def latest_snapshot(self):
            return None

    service = MonitoringService(client, Repo())
    system = await service.get_system()
    assert system["executionState"] == "halted"
    assert system["riskTradingState"] == "halted"
    assert system["killSwitch"] == "triggered"
