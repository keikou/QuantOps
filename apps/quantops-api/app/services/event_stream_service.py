from __future__ import annotations

import asyncio
import json
from typing import Any

from fastapi import WebSocket
from starlette.websockets import WebSocketDisconnect

from app.clients.v12_client import utc_now_iso
from app.services.command_center_service import CommandCenterService


class EventStreamService:
    def __init__(self, command_center_service: CommandCenterService, poll_interval_seconds: float = 1.5) -> None:
        self.command_center_service = command_center_service
        self.poll_interval_seconds = poll_interval_seconds

    async def _build_snapshot(self) -> dict[str, dict[str, Any]]:
        overview = await self.command_center_service.get_overview()
        execution = await self.command_center_service.get_execution_latest()
        runtime_runs = await self.command_center_service.get_runtime_runs(limit=1, window_minutes=5)
        runtime_issues = await self.command_center_service.get_runtime_issues(limit=25, window_minutes=5)
        risk = await self.command_center_service.get_risk_summary()
        strategies = await self.command_center_service.get_strategies()
        system = await self.command_center_service.get_system_summary()
        alerts = self.command_center_service.get_system_alerts()

        top_strategy = None
        if strategies.get("items"):
            top_strategy = sorted(
                strategies["items"],
                key=lambda item: float(item.get("realized_return", 0.0) or 0.0),
                reverse=True,
            )[0]

        alert_items = alerts.get("items") or []
        latest_alert = alert_items[0] if alert_items else None
        latest_run = runtime_runs.get("items", [None])[0] if isinstance(runtime_runs.get("items"), list) and runtime_runs.get("items") else None

        return {
            "pnl_update": {
                "event_type": "pnl_update",
                "as_of": overview.get("as_of") or utc_now_iso(),
                "payload": {
                    "portfolio_value": float(overview.get("portfolio_value", 0.0) or 0.0),
                    "pnl": float(overview.get("pnl", 0.0) or 0.0),
                    "gross_exposure": float(overview.get("gross_exposure", 0.0) or 0.0),
                    "net_exposure": float(overview.get("net_exposure", 0.0) or 0.0),
                    "active_strategies": int(overview.get("active_strategies", 0) or 0),
                },
            },
            "execution_event": {
                "event_type": "execution_event",
                "as_of": execution.get("as_of") or utc_now_iso(),
                "payload": {
                    "fill_rate": float(execution.get("fill_rate", 0.0) or 0.0),
                    "avg_slippage_bps": float(execution.get("avg_slippage_bps", 0.0) or 0.0),
                    "latency_ms_p50": float(execution.get("latency_ms_p50", 0.0) or 0.0),
                    "latency_ms_p95": float(execution.get("latency_ms_p95", 0.0) or 0.0),
                    "venue_score": float(execution.get("venue_score", 0.0) or 0.0),
                },
            },
            "risk_alert": {
                "event_type": "risk_alert",
                "as_of": risk.get("as_of") or utc_now_iso(),
                "payload": {
                    "trading_state": str(risk.get("trading_state", "running") or "running"),
                    "alert_state": str(risk.get("alert_state", "unknown") or "unknown"),
                    "drawdown": float(risk.get("drawdown", 0.0) or 0.0),
                    "open_alerts": int(alerts.get("count", 0) or 0),
                    "latest_alert": latest_alert,
                },
            },
            "strategy_status": {
                "event_type": "strategy_status",
                "as_of": strategies.get("as_of") or utc_now_iso(),
                "payload": {
                    "enabled_count": int(strategies.get("enabled_count", 0) or 0),
                    "top_strategy": top_strategy,
                    "items": strategies.get("items", []),
                },
            },
            "system_status": {
                "event_type": "system_status",
                "as_of": system.get("as_of") or utc_now_iso(),
                "payload": {
                    "system_status": str(system.get("system_status", "unknown") or "unknown"),
                    "execution_status": str(system.get("execution_status", "unknown") or "unknown"),
                    "open_alerts": int(system.get("open_alerts", 0) or 0),
                    "scheduler_jobs": int(system.get("scheduler_jobs", 0) or 0),
                    "services": system.get("services", {}) or {},
                },
            },
            "runtime_run": {
                "event_type": "runtime_run",
                "as_of": (latest_run or {}).get("completed_at") or (latest_run or {}).get("started_at") or utc_now_iso(),
                "payload": latest_run or {},
            },
            "runtime_issue": {
                "event_type": "runtime_issue",
                "as_of": runtime_issues.get("as_of") or utc_now_iso(),
                "payload": {
                    "items": runtime_issues.get("items", []),
                    "count": int(runtime_issues.get("count", 0) or 0),
                    "window_minutes": int(runtime_issues.get("window_minutes", 5) or 5),
                },
            },
        }

    @staticmethod
    def _fingerprint(event: dict[str, Any]) -> str:
        return json.dumps(event.get("payload", {}), sort_keys=True, default=str)

    async def stream(self, websocket: WebSocket) -> None:
        await websocket.accept()
        await websocket.send_json({
            "event_type": "hello",
            "as_of": utc_now_iso(),
            "payload": {"channel": "command-center", "status": "connected"},
        })

        last_fingerprints: dict[str, str] = {}
        try:
            while True:
                snapshot = await self._build_snapshot()
                for event_type, event in snapshot.items():
                    current = self._fingerprint(event)
                    if last_fingerprints.get(event_type) != current:
                        await websocket.send_json(event)
                        last_fingerprints[event_type] = current
                await websocket.send_json({
                    "event_type": "heartbeat",
                    "as_of": utc_now_iso(),
                    "payload": {"status": "alive"},
                })
                await asyncio.sleep(self.poll_interval_seconds)
        except WebSocketDisconnect:
            return
