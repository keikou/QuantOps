from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Iterable

import httpx


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class V12Client:
    """Thin adapter aligned to the actual V12 PhaseH Sprint4 endpoints.

    The bundled V12 code exposes:
    - GET /dashboard/global
    - GET /dashboard/portfolio
    - GET /strategy/registry
    - GET /strategy/risk-budget
    - POST /strategy/allocate-capital
    - GET /execution/quality/latest
    - GET /system/health (and legacy /health)
    - POST /orchestrator/paper/run-cycle

    Several QuantOps control actions from the original scaffold do not yet exist
    as first-class V12 endpoints (strategy pause/resume, runner pause, explicit
    portfolio rebalance route). Those methods return a structured "unsupported"
    payload when V12 is not in mock mode.
    """

    def __init__(self, base_url: str, timeout: float = 10.0, mock_mode: bool = True) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.mock_mode = mock_mode

    async def _request_first(self, method: str, paths: Iterable[str], json: dict[str, Any] | None = None) -> dict[str, Any]:
        path_list = list(paths)
        if self.mock_mode:
            if method.upper() == "GET":
                return self._mock_get(path_list[0])
            return self._mock_post(path_list[0], json or {})

        last_error: Exception | None = None
        async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout) as client:
            for path in path_list:
                try:
                    resp = await client.request(method, path, json=json)
                    if resp.status_code == 404:
                        last_error = httpx.HTTPStatusError("404 fallback", request=resp.request, response=resp)
                        continue
                    resp.raise_for_status()
                    payload = resp.json()
                    if isinstance(payload, dict):
                        payload.setdefault("_endpoint", path)
                    return payload
                except httpx.HTTPStatusError as exc:
                    last_error = exc
                    if exc.response is not None and exc.response.status_code == 404:
                        continue
                    raise
                except Exception as exc:  # pragma: no cover - network/runtime edge
                    last_error = exc
                    raise
        return {
            "status": "missing",
            "message": f"No V12 endpoint matched candidates: {path_list}",
            "error": str(last_error) if last_error else None,
            "as_of": utc_now_iso(),
        }

    def _mock_get(self, path: str) -> dict[str, Any]:
        now = utc_now_iso()
        if path == "/dashboard/global":
            return {
                "dashboard": "global",
                "status": "ok",
                "cards": {
                    "signal_count": 12,
                    "portfolio_count": 3,
                    "fill_rate": 0.94,
                    "strategy_count": 4,
                    "allocated_capital": 0.86,
                    "avg_hit_rate": 0.61,
                    "alpha_registry_count": 18,
                    "top_alpha_rank_score": 0.77,
                },
                "strategy": {
                    "aggregate": {
                        "strategy_count": 4,
                        "allocated_capital": 0.86,
                        "avg_hit_rate": 0.61,
                        "max_drawdown": 0.043,
                    },
                    "drawdown_events": [],
                    "latest_risk_snapshot": {
                        "gross_exposure": 0.91,
                        "net_exposure": 0.24,
                        "per_strategy": [
                            {"strategy_id": "s1", "capital_weight": 0.25, "risk_budget": 0.30, "budget_usage": 0.83, "status": "ok"},
                            {"strategy_id": "s2", "capital_weight": 0.21, "risk_budget": 0.25, "budget_usage": 0.84, "status": "ok"},
                        ],
                    },
                    "latest_global_risk": {"status": "ok", "alerts": []},
                },
                "alpha_factory": {"counts": {"registry": 18}},
                "as_of": now,
            }
        if path == "/dashboard/portfolio":
            return {
                "dashboard": "portfolio",
                "status": "ok",
                "cards": {
                    "portfolio_count": 3,
                    "latest_kept_signals": 7,
                    "gross_exposure_estimate": 0.91,
                },
                "as_of": now,
            }
        if path == "/analytics/portfolio-summary":
            return {
                "status": "ok",
                "portfolio_count": 3,
                "gross_exposure_estimate": 0.91,
                "latest_weight_count": 3,
                "latest": {
                    "input_signals": 12,
                    "kept_signals": 7,
                    "crowding_flags": [],
                    "overlap_penalty_applied": False,
                },
                "as_of": now,
            }
        if path == "/strategy/registry":
            return {
                "status": "ok",
                "strategy_count": 4,
                "enabled_count": 4,
                "strategies": [
                    {"strategy_id": "s1", "strategy_name": "trend", "enabled": True, "capital_weight": 0.25},
                    {"strategy_id": "s2", "strategy_name": "meanrev", "enabled": True, "capital_weight": 0.21},
                    {"strategy_id": "s3", "strategy_name": "carry", "enabled": True, "capital_weight": 0.20},
                    {"strategy_id": "s4", "strategy_name": "breakout", "enabled": True, "capital_weight": 0.20},
                ],
                "as_of": now,
            }
        if path == "/strategy/risk-budget":
            return {
                "status": "ok",
                "risk": {
                    "gross_exposure": 0.91,
                    "net_exposure": 0.24,
                    "per_strategy": [
                        {"strategy_id": "s1", "capital_weight": 0.25, "risk_budget": 0.30, "budget_usage": 0.83, "status": "ok"},
                        {"strategy_id": "s2", "capital_weight": 0.21, "risk_budget": 0.25, "budget_usage": 0.84, "status": "ok"},
                    ],
                    "netting_symbols": [
                        {"symbol": "BTCUSDT", "gross_before": 0.45, "gross_after": 0.33, "net_exposure": 0.12},
                        {"symbol": "ETHUSDT", "gross_before": 0.31, "gross_after": 0.24, "net_exposure": 0.08},
                    ],
                },
                "global": {"status": "ok", "alerts": []},
                "as_of": now,
            }
        if path == "/execution/quality/latest":
            return {
                "status": "ok",
                "fill_rate": 0.94,
                "avg_slippage_bps": 3.8,
                "latency_ms_p50": 112,
                "latency_ms_p95": 265,
                "as_of": now,
            }
        if path in {"/system/health", "/health"}:
            return {
                "status": "ok",
                "mode": "paper",
                "symbols": ["BTCUSDT", "ETHUSDT", "SOLUSDT"],
                "phase": "H",
                "sprint": 4,
                "services": {"api": "ok", "runtime": "ok", "strategy": "ok", "execution": "ok"},
                "as_of": now,
            }
        if path in {"/research-factory/governance-overview", "/governance/overview"}:
            return {
                "status": "ok",
                "promotion_candidates": 2,
                "decay_alerts": 1,
                "pending_approvals": 1,
                "open_incidents": 1,
                "as_of": now,
            }
        if path in {"/research-factory/promotion/evaluate", "/governance/promotion-candidates"}:
            return {"status": "ok", "items": [{"strategy_id": "s1", "score": 0.77, "recommendation": "promote"}], "as_of": now}
        if path in {"/research-factory/live-review", "/governance/live-review"}:
            return {"status": "ok", "items": [{"strategy_id": "s2", "review_state": "watch", "reason": "slight decay"}], "as_of": now}
        if path in {"/research-factory/alpha-decay", "/governance/decay-alerts"}:
            return {"status": "ok", "items": [{"strategy_id": "s2", "severity": "medium", "metric": "hit_rate_drop"}], "as_of": now}
        if path in {"/research-factory/rollback/evaluate", "/governance/rollback-candidates"}:
            return {"status": "ok", "items": [{"strategy_id": "s3", "score": 0.34, "recommendation": "watch"}], "as_of": now}
        if path in {"/execution/shadow-summary", "/analytics/shadow-summary"}:
            return {"status": "ok", "shadow_mode": "paper", "fill_rate": 0.93, "latency_ms_p95": 265, "as_of": now}
        if path == "/portfolio/diagnostics/latest":
            return {
                "status": "ok",
                "diagnostics": {
                    "input_signals": 12,
                    "kept_signals": 7,
                    "crowding_flags": [],
                    "overlap_penalty_applied": False,
                },
                "as_of": now,
            }
        return {"status": "ok", "path": path, "as_of": now}

    def _mock_post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        now = utc_now_iso()
        if path == "/strategy/allocate-capital":
            return {
                "status": "ok",
                "action": "allocate_capital",
                "allocations": [
                    {"strategy_id": "s1", "strategy_name": "trend", "capital_weight": 0.25, "risk_budget": 0.30},
                    {"strategy_id": "s2", "strategy_name": "meanrev", "capital_weight": 0.21, "risk_budget": 0.25},
                ],
                "risk": self._mock_get("/strategy/risk-budget")["risk"],
                "global_risk": self._mock_get("/strategy/risk-budget")["global"],
                "as_of": now,
            }
        if path in {"/research-factory/champion-challenger/run", "/governance/champion-challenger/run"}:
            return {"status": "ok", "winner": "s1", "loser": "s2", "action": "keep_champion", "as_of": now}
        if path == "/orchestrator/paper/run-cycle":
            return {
                "status": "ok",
                "mode": "paper",
                "run": {"run_id": "paper_001", "mode": "paper", "status": "completed", "created_at": now},
                "as_of": now,
            }
        return {"status": "ok", "path": path, "payload": payload, "as_of": now}

    async def get_global_dashboard(self) -> dict[str, Any]:
        return await self._request_first("GET", ["/dashboard/global"])

    async def get_portfolio_dashboard(self) -> dict[str, Any]:
        return await self._request_first("GET", ["/dashboard/portfolio"])

    async def get_portfolio_analytics(self) -> dict[str, Any]:
        return await self._request_first("GET", ["/analytics/portfolio-summary"])

    async def get_strategy_registry(self) -> dict[str, Any]:
        return await self._request_first("GET", ["/strategy/registry"])

    async def get_risk_budget(self) -> dict[str, Any]:
        return await self._request_first("GET", ["/strategy/risk-budget"])

    async def get_execution_quality(self) -> dict[str, Any]:
        return await self._request_first("GET", ["/execution/quality/latest", "/analytics/execution-quality"])

    async def get_system_health(self) -> dict[str, Any]:
        return await self._request_first("GET", ["/system/health", "/health"])

    async def get_portfolio_diagnostics(self) -> dict[str, Any]:
        return await self._request_first("GET", ["/portfolio/diagnostics/latest", "/analytics/portfolio-summary"])

    async def allocate_capital(self) -> dict[str, Any]:
        return await self._request_first("POST", ["/strategy/allocate-capital"])

    async def run_paper_cycle(self) -> dict[str, Any]:
        return await self._request_first("POST", ["/orchestrator/paper/run-cycle"])


    async def get_governance_overview(self) -> dict[str, Any]:
        return await self._request_first("GET", ["/research-factory/governance-overview", "/governance/overview"])

    async def evaluate_promotion(self) -> dict[str, Any]:
        return await self._request_first("GET", ["/research-factory/promotion/evaluate", "/governance/promotion-candidates"])

    async def get_live_review(self) -> dict[str, Any]:
        return await self._request_first("GET", ["/research-factory/live-review", "/governance/live-review"])

    async def get_alpha_decay(self) -> dict[str, Any]:
        return await self._request_first("GET", ["/research-factory/alpha-decay", "/governance/decay-alerts"])

    async def evaluate_rollback(self) -> dict[str, Any]:
        return await self._request_first("GET", ["/research-factory/rollback/evaluate", "/governance/rollback-candidates"])

    async def run_champion_challenger(self) -> dict[str, Any]:
        return await self._request_first("POST", ["/research-factory/champion-challenger/run", "/governance/champion-challenger/run"])

    async def get_shadow_summary(self) -> dict[str, Any]:
        return await self._request_first("GET", ["/execution/shadow-summary", "/analytics/shadow-summary"])

    async def unsupported_action(self, action: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        return {
            "status": "unsupported_by_v12_phaseh_sprint4",
            "action": action,
            "payload": payload or {},
            "supported_endpoints": {
                "read": [
                    "/dashboard/global",
                    "/dashboard/portfolio",
                    "/strategy/registry",
                    "/strategy/risk-budget",
                    "/execution/quality/latest",
                    "/system/health",
                ],
                "write": [
                    "/strategy/allocate-capital",
                    "/orchestrator/paper/run-cycle",
                ],
            },
            "as_of": utc_now_iso(),
        }
