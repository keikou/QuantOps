from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Iterable

import httpx
import logging

from app.core.request_context import current_request_id, current_request_path


logger = logging.getLogger("uvicorn.error")
TARGET_PATHS = {"/api/v1/dashboard/overview", "/api/v1/portfolio/positions"}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class V12Client:
    def __init__(self, base_url: str, timeout: float = 10.0, mock_mode: bool = True) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.mock_mode = mock_mode

    async def _request_first(
        self,
        method: str,
        paths: Iterable[str],
        json: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        path_list = list(paths)
        if self.mock_mode:
            if method.upper() == "GET":
                return self._mock_get(path_list[0])
            return self._mock_post(path_list[0], json or {})

        last_error: Exception | None = None
        async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout) as client:
            for path in path_list:
                started = datetime.now(timezone.utc)
                try:
                    resp = await client.request(method, path, json=json)
                    duration_ms = round((datetime.now(timezone.utc) - started).total_seconds() * 1000.0, 2)
                    log_fn = logger.warning if current_request_path() in TARGET_PATHS else logger.info
                    log_fn(
                        "v12_request_complete request_id=%s quantops_path=%s method=%s upstream_path=%s status=%s duration_ms=%s",
                        current_request_id(),
                        current_request_path(),
                        method.upper(),
                        path,
                        resp.status_code,
                        duration_ms,
                    )
                    if resp.status_code == 404:
                        last_error = httpx.HTTPStatusError("404 fallback", request=resp.request, response=resp)
                        continue
                    resp.raise_for_status()
                    payload = resp.json()
                    if isinstance(payload, dict):
                        payload.setdefault("_endpoint", path)
                    return payload if isinstance(payload, dict) else {"data": payload, "_endpoint": path}
                except httpx.HTTPStatusError as exc:
                    last_error = exc
                    duration_ms = round((datetime.now(timezone.utc) - started).total_seconds() * 1000.0, 2)
                    logger.warning(
                        "v12_request_http_error request_id=%s quantops_path=%s method=%s upstream_path=%s status=%s duration_ms=%s",
                        current_request_id(),
                        current_request_path(),
                        method.upper(),
                        path,
                        exc.response.status_code if exc.response is not None else None,
                        duration_ms,
                    )
                    if exc.response is not None and exc.response.status_code in {404, 500, 502, 503, 504}:
                        continue
                except Exception as exc:
                    last_error = exc
                    duration_ms = round((datetime.now(timezone.utc) - started).total_seconds() * 1000.0, 2)
                    logger.warning(
                        "v12_request_exception request_id=%s quantops_path=%s method=%s upstream_path=%s duration_ms=%s error=%s",
                        current_request_id(),
                        current_request_path(),
                        method.upper(),
                        path,
                        duration_ms,
                        repr(exc),
                    )
                    continue

        return {
            "status": "degraded",
            "message": f"All upstream endpoints failed for {path_list}",
            "error": str(last_error) if last_error else None,
            "as_of": utc_now_iso(),
            "items": [],
            "positions": [],
            "strategies": [],
            "alerts": [],
            "risk": {},
            "global": {},
        }

    async def get_global_dashboard(self) -> dict[str, Any]:
        return await self._request_first("GET", ["/dashboard/global"])

    async def get_portfolio_dashboard(self) -> dict[str, Any]:
        return await self._request_first("GET", ["/portfolio/overview", "/dashboard/portfolio"])

    async def get_portfolio_analytics(self) -> dict[str, Any]:
        return await self._request_first("GET", ["/portfolio/diagnostics/latest", "/portfolio/overview"])

    async def get_portfolio_diagnostics(self) -> dict[str, Any]:
        return await self._request_first("GET", ["/portfolio/diagnostics/latest", "/portfolio/overview"])

    async def get_portfolio_positions(self) -> dict[str, Any]:
        return await self._request_first("GET", ["/portfolio/positions/latest", "/portfolio/overview"])

    async def get_runtime_status(self) -> dict[str, Any]:
        return await self._request_first("GET", ["/runtime/status", "/runtime/runs?limit=1", "/health"])

    async def get_runtime_runs(self, limit: int = 20) -> dict[str, Any]:
        return await self._request_first("GET", [f"/runtime/runs?limit={int(limit)}"])

    async def get_runtime_run(self, run_id: str) -> dict[str, Any]:
        return await self._request_first("GET", [f"/runtime/runs/{run_id}"])

    async def get_runtime_events_latest(self, limit: int = 50) -> dict[str, Any]:
        return await self._request_first("GET", [f"/runtime/events/latest?limit={int(limit)}"])

    async def get_runtime_events_by_run(self, run_id: str, limit: int = 50) -> dict[str, Any]:
        return await self._request_first("GET", [f"/runtime/events/by-run/{run_id}?limit={int(limit)}"])

    async def get_runtime_reasons_latest(self, limit: int = 50) -> dict[str, Any]:
        return await self._request_first("GET", [f"/runtime/reasons/latest?limit={int(limit)}"])

    async def get_runtime_reasons_by_run(self, run_id: str, limit: int = 50) -> dict[str, Any]:
        return await self._request_first("GET", [f"/runtime/reasons/by-run/{run_id}?limit={int(limit)}"])

    async def get_strategy_registry(self) -> dict[str, Any]:
        return await self._request_first("GET", ["/strategy/registry"])

    async def get_strategy_risk_budget(self) -> dict[str, Any]:
        return await self._request_first("GET", ["/strategy/risk-budget"])

    async def get_risk_budget(self) -> dict[str, Any]:
        return await self._request_first("GET", ["/strategy/risk-budget", "/risk/latest"])

    async def allocate_capital(self, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        return await self._request_first("POST", ["/strategy/allocate-capital"], json=payload or {})

    async def unsupported_action(self, action: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        payload = payload or {}
        strategy_id = str(payload.get("strategy_id", "") or "")
        endpoint_map: dict[str, list[str]] = {
            "start_strategy": [
                f"/strategy/{strategy_id}/start",
                "/strategy/lifecycle/start",
                f"/runtime/strategies/{strategy_id}/start",
            ],
            "stop_strategy": [
                f"/strategy/{strategy_id}/stop",
                "/strategy/lifecycle/stop",
                f"/runtime/strategies/{strategy_id}/stop",
            ],
            "pause_strategy": [
                f"/strategy/{strategy_id}/pause",
                "/strategy/lifecycle/pause",
                f"/runtime/strategies/{strategy_id}/pause",
            ],
            "reload_strategy": [
                f"/strategy/{strategy_id}/reload",
                "/strategy/lifecycle/reload",
                f"/runtime/strategies/{strategy_id}/reload",
            ],
            "kill_switch": [
                "/risk/kill-switch",
                "/runtime/kill-switch",
                "/system/kill-switch",
            ],
        }
        paths = endpoint_map.get(action)
        if paths:
            response = await self._request_first("POST", paths, json=payload)
            status = str(response.get("status", "") or "")
            if status and status not in {"missing", "unsupported"}:
                response.setdefault("action", action)
                response.setdefault("payload", payload)
                return response
        return {
            "status": "accepted",
            "adapter": "quantops-local-fallback",
            "action": action,
            "payload": payload,
            "message": "Lifecycle command accepted by QuantOps fallback adapter.",
            "as_of": utc_now_iso(),
        }

    async def get_execution_quality_latest(self) -> dict[str, Any]:
        return await self._request_first("GET", ["/execution/quality/latest"])

    async def get_execution_quality(self) -> dict[str, Any]:
        return await self._request_first("GET", ["/execution/quality/latest_summary", "/execution/quality/latest"])

    async def get_execution_planner_latest(self) -> dict[str, Any]:
        return await self._request_first("GET", ["/execution/planner/latest", "/execution/plans?limit=20"])

    async def get_execution_plans_latest(self) -> dict[str, Any]:
        return await self._request_first("GET", ["/execution/plans/latest"])

    async def get_execution_plans_by_run(self, run_id: str) -> dict[str, Any]:
        return await self._request_first("GET", [f"/execution/plans/by-run/{run_id}"])

    async def get_execution_orders(self, limit: int | None = None) -> dict[str, Any]:
        suffix = f"?limit={int(limit)}" if limit is not None else ""
        return await self._request_first("GET", [f"/execution/orders{suffix}", f"/execution/orders/latest{suffix}", "/execution/orders", "/execution/orders/latest"])

    async def get_execution_fills(self, limit: int | None = None) -> dict[str, Any]:
        suffix = f"?limit={int(limit)}" if limit is not None else ""
        return await self._request_first("GET", [f"/execution/fills{suffix}", f"/execution/fills/latest{suffix}", "/execution/fills", "/execution/fills/latest"])

    async def get_execution_state_latest(self) -> dict[str, Any]:
        return await self._request_first("GET", ["/execution/state/latest"])

    async def get_execution_block_reasons_latest(self) -> dict[str, Any]:
        return await self._request_first("GET", ["/execution/block-reasons/latest"])

    async def get_execution_bridge_latest(self) -> dict[str, Any]:
        return await self._request_first("GET", ["/execution/bridge/latest"])

    async def get_execution_bridge_by_run(self, run_id: str) -> dict[str, Any]:
        return await self._request_first("GET", [f"/execution/bridge/by-run/{run_id}"])

    async def get_health(self) -> dict[str, Any]:
        return await self._request_first("GET", ["/system/health", "/health"])

    async def get_system_health(self) -> dict[str, Any]:
        return await self._request_first("GET", ["/system/health", "/health"])

    async def run_runtime_once(self, mode: str = "paper") -> dict[str, Any]:
        return await self._request_first("POST", [f"/runtime/run-once?mode={mode}", "/runtime/run-once"], json={"mode": mode})

    async def pause_runtime(self, note: str | None = None) -> dict[str, Any]:
        payload = {"note": note} if note else {}
        return await self._request_first("POST", ["/runtime/pause", "/runtime/kill-switch"], json=payload)

    async def resume_runtime(self, note: str | None = None) -> dict[str, Any]:
        payload = {"note": note} if note else {}
        return await self._request_first("POST", ["/runtime/resume"], json=payload)

    async def kill_switch_runtime(self, note: str | None = None) -> dict[str, Any]:
        payload = {"note": note} if note else {}
        return await self._request_first("POST", ["/runtime/kill-switch", "/risk/kill-switch", "/system/kill-switch"], json=payload)

    async def run_paper_cycle(self) -> dict[str, Any]:
        return await self.run_runtime_once(mode="paper")

    async def get_sprint5c_risk_latest(self) -> dict[str, Any]:
        return await self._request_first("GET", ["/risk/latest"])

    async def get_sprint5c_risk_history(self, limit: int = 100) -> dict[str, Any]:
        return await self._request_first("GET", [f"/risk/history?limit={limit}"])

    async def get_sprint5c_analytics_performance(self) -> dict[str, Any]:
        return await self._request_first("GET", ["/analytics/performance"])

    async def get_sprint5c_analytics_alpha(self) -> dict[str, Any]:
        return await self._request_first("GET", ["/analytics/alpha"])

    async def get_sprint5c_governance_budgets(self) -> dict[str, Any]:
        return await self._request_first("GET", ["/governance/budgets"])

    async def get_sprint5c_governance_regime(self) -> dict[str, Any]:
        return await self._request_first("GET", ["/governance/regime"])

    async def get_sprint5c_scheduler_jobs(self) -> dict[str, Any]:
        return await self._request_first("GET", ["/scheduler/jobs"])

    async def get_sprint5c_scheduler_runs(self) -> dict[str, Any]:
        return await self._request_first("GET", ["/scheduler/runs"])

    async def run_sprint5c_cycle(self) -> dict[str, Any]:
        return await self._request_first("POST", ["/runtime/run-once"], json={})

    async def get_current_mode(self) -> dict[str, Any]:
        return await self._request_first("GET", ["/runtime/modes/current"])

    async def get_mode_config(self) -> dict[str, Any]:
        return await self._request_first("GET", ["/runtime/modes"])

    async def get_incidents_latest_upstream(self) -> dict[str, Any]:
        return await self._request_first("GET", ["/incidents/latest"])

    async def get_incidents_history_upstream(self, limit: int = 100) -> dict[str, Any]:
        return await self._request_first("GET", [f"/incidents/history?limit={limit}"])

    async def get_acceptance_status(self) -> dict[str, Any]:
        return await self._request_first("GET", ["/acceptance/status"])

    async def get_acceptance_checks(self) -> dict[str, Any]:
        return await self._request_first("GET", ["/acceptance/checks"])

    async def run_acceptance(self) -> dict[str, Any]:
        return await self._request_first("POST", ["/acceptance/run"], json={})

    async def run_with_mode(self, mode: str) -> dict[str, Any]:
        return await self._request_first("POST", ["/runtime/run-with-mode"], json={"mode": mode})


    async def get_equity_history(self) -> dict[str, Any]:
        return await self._request_first("GET", ["/portfolio/equity-history"])

    async def get_shadow_summary(self) -> dict[str, Any]:
        return await self._request_first("GET", ["/analytics/shadow-summary"])

    def _mock_get(self, path: str) -> dict[str, Any]:
        positions = [
            {"symbol": "BTCUSDT", "side": "long", "weight": 0.40, "notional": 400000.0, "pnl": 0.015, "run_id": "mock", "timestamp": utc_now_iso()},
            {"symbol": "ETHUSDT", "side": "short", "weight": -0.35, "notional": -350000.0, "pnl": 0.010, "run_id": "mock", "timestamp": utc_now_iso()},
            {"symbol": "SOLUSDT", "side": "long", "weight": 0.25, "notional": 250000.0, "pnl": 0.008, "run_id": "mock", "timestamp": utc_now_iso()},
        ]
        if path == "/dashboard/global":
            return {
                "status": "ok",
                "cards": {"signal_count": 12, "strategy_count": 4, "allocated_capital": 1_000_000},
                "strategy": {
                    "aggregate": {"allocated_capital": 1_000_000, "avg_realized_return": 0.012, "avg_hit_rate": 0.57},
                    "latest_risk_snapshot": {"gross_exposure": 1.0, "net_exposure": 0.30},
                    "drawdown_events": [],
                },
                "as_of": utc_now_iso(),
            }
        if path in {"/dashboard/portfolio", "/portfolio/overview"}:
            return {
                "status": "ok",
                "snapshot": {"gross_exposure": 1.0, "net_exposure": 0.30, "cash_fraction": 0.0, "run_id": "mock"},
                "positions": positions,
                "cards": {"portfolio_count": 3, "gross_exposure_estimate": 1.0},
                "as_of": utc_now_iso(),
            }
        if path == "/portfolio/positions/latest":
            return {"status": "ok", "items": positions, "run_id": "mock", "as_of": utc_now_iso()}
        if path in {"/portfolio/diagnostics/latest"}:
            return {"status": "ok", "diagnostics": {"kept_signals": 9}, "latest": {"kept_signals": 9}, "as_of": utc_now_iso()}
        if path == "/runtime/status":
            return {"status": "ok", "mock_mode": True, "latest_run_id": "mock", "latest_position_count": len(positions), "latest_signal_count": 3, "as_of": utc_now_iso()}
        if path == "/strategy/registry":
            return {
                "status": "ok",
                "enabled_count": 3,
                "strategies": [
                    {"strategy_id": "s1", "strategy_name": "alpha_1", "capital_weight": 0.4, "realized_return": 0.015},
                    {"strategy_id": "s2", "strategy_name": "alpha_2", "capital_weight": 0.35, "realized_return": 0.010},
                    {"strategy_id": "s3", "strategy_name": "alpha_3", "capital_weight": 0.25, "realized_return": 0.008},
                ],
                "as_of": utc_now_iso(),
            }
        if path in {"/strategy/risk-budget", "/risk/latest"}:
            return {
                "status": "ok",
                "risk": {
                    "gross_exposure": 1.0,
                    "net_exposure": 0.30,
                    "per_strategy": [
                        {"strategy_id": "s1", "budget_usage": 0.74},
                        {"strategy_id": "s2", "budget_usage": 0.79},
                        {"strategy_id": "s3", "budget_usage": 0.68},
                    ],
                },
                "global": {"status": "ok", "alerts": []},
                "as_of": utc_now_iso(),
            }
        if path in {"/execution/quality/latest", "/execution/quality/latest_summary"}:
            return {
                "status": "ok",
                "run_id": "mock",
                "fill_rate": 1.0,
                "avg_slippage_bps": 1.2,
                "latency_ms_p50": 35.0,
                "latency_ms_p95": 80.0,
                "as_of": utc_now_iso(),
            }
        if path in {"/execution/orders", "/execution/orders/latest"}:
            return {"status": "ok", "items": [], "as_of": utc_now_iso()}
        if path in {"/execution/fills", "/execution/fills/latest"}:
            return {"status": "ok", "items": [], "as_of": utc_now_iso()}
        if path == "/execution/state/latest":
            return {
                "status": "ok",
                "trading_state": "running",
                "execution_state": "idle",
                "block_reasons": [],
                "active_plan_count": 0,
                "open_order_count": 0,
                "as_of": utc_now_iso(),
            }
        if path == "/execution/block-reasons/latest":
            return {"status": "ok", "items": [], "as_of": utc_now_iso()}
        if path in {"/system/health", "/health"}:
            return {"status": "ok", "mode": "paper", "services": {"api": "ok", "runtime": "ok", "worker": "ok"}, "as_of": utc_now_iso()}
        if path == "/analytics/shadow-summary":
            return {"status": "ok", "net_shadow_pnl": 123.45, "as_of": utc_now_iso()}
        return {"status": "ok", "as_of": utc_now_iso()}

    def _mock_post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        if "run-once" in path or path == "/orchestrator/paper/run-cycle":
            return {"status": "ok", "run_id": "mock-run", "mode": payload.get("mode", "paper"), "submitted": True, "as_of": utc_now_iso()}
        return {"status": "accepted", "path": path, "payload": payload, "as_of": utc_now_iso()}
