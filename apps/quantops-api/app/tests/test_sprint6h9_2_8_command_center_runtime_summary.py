from __future__ import annotations

import asyncio

from app.services.command_center_service import CommandCenterService


class _RuntimeV12Client:
    async def get_execution_bridge_latest(self) -> dict:
        return {
            "status": "ok",
            "run_id": "run-123",
            "cycle_id": "cycle-123",
            "bridge_state": "submitted_no_fill",
            "planned_count": 2,
            "submitted_count": 2,
            "blocked_count": 0,
            "filled_count": 0,
            "event_chain_complete": True,
            "latest_reason_code": "ORDER_REJECTED",
            "latest_reason_summary": "Orders submitted but no fills were recorded.",
            "blocking_component": "execution_bridge",
            "degraded_flags": ["stale_market_data"],
            "operator_message": "The cycle reached the market but did not fill.",
            "last_transition_at": "2026-03-23T00:00:09+00:00",
        }

    async def get_execution_plans_latest(self) -> dict:
        return {
            "run_id": "run-123",
            "cycle_id": "cycle-123",
            "planner_status": "generated",
            "generated_at": "2026-03-23T00:00:02+00:00",
        }

    async def get_runtime_events_latest(self, limit: int = 20) -> dict:
        return {
            "items": [
                {
                    "event_type": "cycle_completed",
                    "summary": "Cycle completed.",
                    "severity": "info",
                    "status": "ok",
                    "timestamp": "2026-03-23T00:00:10+00:00",
                },
                {
                    "event_type": "portfolio_updated",
                    "summary": "Portfolio state updated.",
                    "severity": "info",
                    "status": "ok",
                    "timestamp": "2026-03-23T00:00:08+00:00",
                },
                {
                    "event_type": "fill_recorded",
                    "summary": "Latest successful fill from prior cycle.",
                    "severity": "info",
                    "status": "ok",
                    "timestamp": "2026-03-23T00:00:06+00:00",
                },
                {
                    "event_type": "order_submitted",
                    "summary": "Submitted order.",
                    "severity": "info",
                    "status": "ok",
                    "timestamp": "2026-03-23T00:00:05+00:00",
                },
            ]
        }

    async def get_runtime_reasons_latest(self, limit: int = 10) -> dict:
        return {
            "items": [
                {
                    "reason_code": "ORDER_REJECTED",
                    "summary": "Orders submitted but no fills were recorded.",
                    "details": {"blocking_component": "execution_bridge"},
                }
            ]
        }


def _build_service() -> CommandCenterService:
    return CommandCenterService(
        v12_client=_RuntimeV12Client(),  # type: ignore[arg-type]
        dashboard_service=None,  # type: ignore[arg-type]
        portfolio_service=None,  # type: ignore[arg-type]
        risk_service=None,  # type: ignore[arg-type]
        analytics_service=None,  # type: ignore[arg-type]
        monitoring_service=None,  # type: ignore[arg-type]
        alert_service=None,  # type: ignore[arg-type]
        scheduler_service=None,  # type: ignore[arg-type]
        control_service=None,  # type: ignore[arg-type]
        analytics_repository=None,  # type: ignore[arg-type]
        audit_repository=None,  # type: ignore[arg-type]
        risk_repository=None,  # type: ignore[arg-type]
        notification_service=None,  # type: ignore[arg-type]
    )


def test_command_center_runtime_latest_exposes_operator_summary_fields() -> None:
    payload = asyncio.run(_build_service().get_runtime_latest())

    assert payload["run_id"] == "run-123"
    assert payload["operator_state"] == "submitted_no_fill"
    assert payload["degraded"] is True
    assert payload["latest_reason_code"] == "ORDER_REJECTED"
    assert payload["last_successful_fill_at"] == "2026-03-23T00:00:06+00:00"
    assert payload["last_successful_portfolio_update_at"] == "2026-03-23T00:00:08+00:00"
    assert payload["last_cycle_completed_at"] == "2026-03-23T00:00:10+00:00"
