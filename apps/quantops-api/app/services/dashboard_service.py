from __future__ import annotations

import asyncio
from datetime import datetime, timezone
import logging
import time

from app.clients.v12_client import V12Client, utc_now_iso
from app.repositories.scheduler_repository import SchedulerRepository
from app.services.alert_service import AlertService
from app.services.equity_breakdown import compute_equity_breakdown


class _NullAlertService:
    def evaluate_rules(self) -> None:
        return None

    def list_alerts(self) -> dict:
        return {"items": [], "count": 0, "open_count": 0}


logger = logging.getLogger(__name__)


class DashboardService:
    OVERVIEW_TTL_SECONDS = 5.0
    OVERVIEW_PRIMARY_TIMEOUT_SECONDS = 3.5
    OVERVIEW_AUX_TIMEOUT_SECONDS = 1.5
    OVERVIEW_PORTFOLIO_CACHE_TTL_SECONDS = 15.0
    OVERVIEW_RUNTIME_CACHE_TTL_SECONDS = 15.0
    OVERVIEW_REGISTRY_CACHE_TTL_SECONDS = 60.0

    def __init__(
        self,
        v12_client: V12Client,
        scheduler_repository: SchedulerRepository,
        alert_service: AlertService | None = None,
    ) -> None:
        self.v12_client = v12_client
        self.scheduler_repository = scheduler_repository
        self.alert_service = alert_service or _NullAlertService()
        self._overview_cache: dict | None = None
        self._overview_refresh_task: asyncio.Task | None = None
        self._overview_inflight_task: asyncio.Task | None = None
        self._overview_portfolio_cache: dict | None = None
        self._overview_portfolio_cache_at: float = 0.0
        self._overview_runtime_cache: dict | None = None
        self._overview_runtime_cache_at: float = 0.0
        self._overview_registry_cache: dict | None = None
        self._overview_registry_cache_at: float = 0.0

    @classmethod
    def _freshness_anchor(cls, payload: dict | None) -> object:
        if not isinstance(payload, dict):
            return None
        return payload.get("source_snapshot_time") or payload.get("as_of")

    @staticmethod
    def _as_dict(payload: object) -> dict:
        return payload if isinstance(payload, dict) else {}

    @staticmethod
    def _safe_float(value: object, default: float = 0.0) -> float:
        try:
            if value is None:
                return default
            return float(value)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _safe_int(value: object, default: int = 0) -> int:
        try:
            if value is None or value == "":
                return default
            return int(value)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _snapshot_age_sec(value: object) -> float | None:
        if not value:
            return None
        try:
            ts = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            else:
                ts = ts.astimezone(timezone.utc)
            return round(max(0.0, (datetime.now(timezone.utc) - ts).total_seconds()), 3)
        except Exception:
            return None

    @classmethod
    def _is_fresh_as_of(cls, value: object) -> bool:
        age = cls._snapshot_age_sec(value)
        return age is not None and age <= cls.OVERVIEW_TTL_SECONDS

    def _decorate_overview_response(self, payload: dict, *, build_status: str) -> dict:
        result = dict(payload)
        result["rebuilt_at"] = result.get("rebuilt_at") or utc_now_iso()
        source_snapshot_time = result.get("source_snapshot_time") or result.get("as_of")
        result["source_snapshot_time"] = source_snapshot_time
        result["data_freshness_sec"] = self._snapshot_age_sec(source_snapshot_time)
        result["build_status"] = build_status
        stable_value = {
            "total_equity": result.get("total_equity"),
            "balance": result.get("balance"),
            "used_margin": result.get("used_margin"),
            "free_margin": result.get("free_margin"),
            "gross_exposure": result.get("gross_exposure"),
            "net_exposure": result.get("net_exposure"),
            "active_strategies": result.get("active_strategies"),
            "open_alerts": result.get("open_alerts"),
            "running_jobs": result.get("running_jobs"),
        }
        result["stable_value"] = stable_value
        result["live_delta"] = {
            "alerts_window": None,
            "jobs_window": None,
        }
        result["display_value"] = dict(stable_value)
        return result

    async def _call_with_timeout(self, operation, timeout_seconds: float) -> dict:
        try:
            result = await asyncio.wait_for(operation, timeout=timeout_seconds)
        except Exception:
            return {}
        return result if isinstance(result, dict) else {}

    @staticmethod
    def _is_timed_cache_fresh(cached_at: float, ttl_seconds: float) -> bool:
        return cached_at > 0.0 and (time.perf_counter() - cached_at) <= ttl_seconds

    async def _get_optional_aux_payload(
        self,
        *,
        cache_name: str,
        operation_factory,
        ttl_seconds: float,
        timeout_seconds: float,
    ) -> dict:
        payload_attr = f"_overview_{cache_name}_cache"
        cached_at_attr = f"_overview_{cache_name}_cache_at"
        cached_payload = getattr(self, payload_attr)
        cached_at = float(getattr(self, cached_at_attr, 0.0) or 0.0)
        if isinstance(cached_payload, dict) and self._is_timed_cache_fresh(cached_at, ttl_seconds):
            return dict(cached_payload)

        payload = await self._call_with_timeout(operation_factory(), timeout_seconds)
        if payload:
            setattr(self, payload_attr, dict(payload))
            setattr(self, cached_at_attr, time.perf_counter())
            return payload

        if isinstance(cached_payload, dict):
            return dict(cached_payload)
        return {}

    def _overview_has_truth(self, payload: dict) -> bool:
        return any(
            (
                float(payload.get("total_equity", 0.0) or 0.0) > 0.0,
                int(payload.get("active_strategies", 0) or 0) > 0,
                int(payload.get("open_alerts", 0) or 0) > 0,
                bool(payload.get("latest_run_id")),
            )
        )

    def _store_overview_cache(self, payload: dict) -> dict:
        self._overview_cache = dict(payload)
        return payload

    async def _refresh_overview_cache(self) -> dict:
        payload = await self._build_overview_live()
        if self._overview_has_truth(payload):
            self._store_overview_cache(payload)
        return payload

    async def _await_overview_live(self) -> dict:
        task = self._overview_inflight_task
        if task is None or task.done():
            task = asyncio.create_task(self._build_overview_live())
            self._overview_inflight_task = task
        try:
            return await task
        finally:
            if self._overview_inflight_task is task and task.done():
                self._overview_inflight_task = None

    def _schedule_overview_refresh(self) -> None:
        task = self._overview_refresh_task
        if task is not None and not task.done():
            return
        self._overview_refresh_task = asyncio.create_task(self._refresh_overview_cache())
        self._overview_refresh_task.add_done_callback(lambda finished: finished.exception())

    @staticmethod
    def _first_present_key(payload: dict, *keys: str) -> str | None:
        for key in keys:
            if key in payload and payload.get(key) is not None:
                return key
        return None

    async def _build_overview_live(self) -> dict:
        started = time.perf_counter()

        # fast portfolio 型:
        # overview に必要な最小限の upstream だけ使う
        (
            dashboard_payload,
            runtime_payload,
            registry_payload,
        ) = await asyncio.gather(
            self._get_optional_aux_payload(
                cache_name="portfolio",
                operation_factory=self.v12_client.get_portfolio_dashboard,
                ttl_seconds=self.OVERVIEW_PORTFOLIO_CACHE_TTL_SECONDS,
                timeout_seconds=self.OVERVIEW_PRIMARY_TIMEOUT_SECONDS,
            ),
            self._get_optional_aux_payload(
                cache_name="runtime",
                operation_factory=self.v12_client.get_runtime_status,
                ttl_seconds=self.OVERVIEW_RUNTIME_CACHE_TTL_SECONDS,
                timeout_seconds=self.OVERVIEW_AUX_TIMEOUT_SECONDS,
            ),
            self._get_optional_aux_payload(
                cache_name="registry",
                operation_factory=self.v12_client.get_strategy_registry,
                ttl_seconds=self.OVERVIEW_REGISTRY_CACHE_TTL_SECONDS,
                timeout_seconds=self.OVERVIEW_AUX_TIMEOUT_SECONDS,
            ),
        )

        portfolio_dashboard = self._as_dict(dashboard_payload)
        portfolio = portfolio_dashboard
        runtime = self._as_dict(runtime_payload)

        summary = (
            portfolio_dashboard.get("summary")
            if isinstance(portfolio_dashboard.get("summary"), dict)
            else portfolio_dashboard
        )
        summary = summary if isinstance(summary, dict) else {}
        summary_total_equity = self._safe_float(
            summary.get("total_equity") or summary.get("portfolio_value") or 0.0
        )

        items = portfolio.get("items") or portfolio.get("positions") or []
        if not isinstance(items, list):
            items = []

        weights: list[float] = []
        total_pnl = 0.0

        for row in items:
            if not isinstance(row, dict):
                continue
            weight = self._safe_float(row.get("weight", row.get("target_weight", 0.0)))
            side = str(row.get("side", "long") or "long").lower()
            if weight == 0.0 and summary_total_equity > 0.0:
                notional = self._safe_float(
                    row.get("exposure_notional", row.get("notional_usd", row.get("notional", 0.0)))
                )
                weight = notional / max(abs(summary_total_equity), 1e-9)
            if side == "short" and weight > 0:
                weight = -weight
            weights.append(weight)
            total_pnl += self._safe_float(row.get("pnl", row.get("unrealized_pnl", 0.0)))

        try:
            breakdown = compute_equity_breakdown(portfolio_dashboard, portfolio)
        except Exception:
            logger.exception("equity_breakdown_failed_dashboard_fast")
            summary_balance = self._safe_float(
                summary.get("cash_balance")
                or summary.get("balance")
                or summary.get("cash")
                or summary.get("free_cash")
                or 0.0
            )
            summary_used_margin = self._safe_float(summary.get("used_margin") or 0.0)
            summary_unrealized = self._safe_float(summary.get("unrealized_pnl") or summary.get("unrealized") or 0.0)
            summary_total_equity = self._safe_float(
                summary.get("total_equity")
                or summary.get("portfolio_value")
                or (summary_balance + self._safe_float(summary.get("market_value") or 0.0))
                or 0.0
            )
            breakdown = {
                "balance": round(summary_balance, 2),
                "used_margin": round(summary_used_margin, 2),
                "free_margin": round(summary_total_equity - summary_used_margin, 2),
                "unrealized": round(summary_unrealized, 2),
                "total_equity": round(summary_total_equity, 2),
            }

        total_equity = self._safe_float(breakdown.get("total_equity"))

        gross_exposure = self._safe_float(
            summary.get("gross_exposure", summary.get("grossExposure", 0.0))
        )
        net_exposure = self._safe_float(
            summary.get("net_exposure", summary.get("netExposure", 0.0))
        )

        if gross_exposure == 0.0 and weights:
            gross_exposure = sum(abs(v) for v in weights)
        if net_exposure == 0.0 and weights:
            net_exposure = sum(weights)

        # pnl は shadow summary を呼ばず、summary -> positions 合計の順で fallback
        realized_pnl = self._safe_float(summary.get("realized_pnl", 0.0))
        unrealized_pnl_summary = self._safe_float(summary.get("unrealized_pnl", 0.0))
        pnl = realized_pnl + unrealized_pnl_summary
        if pnl == 0.0:
            pnl = total_pnl

        # strategy_registry は必須ではないので失敗しても overview を遅く/壊さない
        registry = self._as_dict(registry_payload)
        active_strategies = int(
            registry.get("enabled_count")
            or len(registry.get("strategies") or [])
            or len(items)
        )

        # scheduler jobs はローカル参照のみ
        try:
            job_rows = self.scheduler_repository.list_jobs()
        except Exception:
            logger.exception("dashboard_scheduler_jobs_failed")
            job_rows = []

        running_jobs = sum(
            1
            for row in job_rows
            if str((row or {}).get("status", "idle")).lower() in {"running", "active"}
        )

        # fast path: read API で evaluate_rules は実行しない
        try:
            alerts_payload = self.alert_service.list_alerts()
        except Exception:
            logger.exception("dashboard_alerts_read_failed")
            alerts_payload = {"items": [], "count": 0, "open_count": 0}

        alerts = alerts_payload.get("items") or []
        open_alert_count = int(
            alerts_payload.get("open_count", alerts_payload.get("count", 0)) or 0
        )

        as_of = (
            runtime.get("as_of")
            or portfolio_dashboard.get("as_of")
            or portfolio.get("as_of")
            or utc_now_iso()
        )

        result = {
            "portfolio_value": round(total_equity, 2),
            "total_equity": round(total_equity, 2),
            "balance": round(self._safe_float(breakdown.get("balance")), 2),
            "used_margin": round(self._safe_float(breakdown.get("used_margin")), 2),
            "free_margin": round(self._safe_float(breakdown.get("free_margin")), 2),
            "unrealized": round(self._safe_float(breakdown.get("unrealized")), 2),
            "pnl": round(pnl, 6),
            "gross_exposure": round(gross_exposure, 6),
            "net_exposure": round(net_exposure, 6),
            "leverage": round(gross_exposure, 6),
            "active_strategies": int(active_strategies),
            "alerts": alerts,
            "open_alerts": int(open_alert_count),
            "running_jobs": int(running_jobs),
            "mock_mode": runtime.get("mock_mode"),
            "latest_run_id": runtime.get("latest_run_id"),
            "latest_execution_timestamp": None,
            "as_of": as_of,
            "source_snapshot_time": (
                summary.get("source_snapshot_time")
                or summary.get("as_of")
                or portfolio_dashboard.get("as_of")
                or portfolio.get("as_of")
                or as_of
            ),
            "active_snapshot_version": self._safe_int(
                summary.get("active_snapshot_version")
                or (portfolio_dashboard.get("snapshot") or {}).get("active_snapshot_version"),
                default=0,
            ) or None,
            "position_row_count": int(summary.get("position_row_count") or len(items)),
            "strategy_row_count": int(summary.get("strategy_row_count") or 0),
        }

        duration_ms = round((time.perf_counter() - started) * 1000.0, 2)
        logger.info(
            "dashboard_overview_fast_built",
            extra={
                "duration_ms": duration_ms,
                "positions_count": len(items),
                "active_strategies": result["active_strategies"],
                "running_jobs": result["running_jobs"],
            },
        )

        return result

    async def get_overview(self) -> dict:
        cached = self._overview_cache
        freshness_anchor = self._freshness_anchor(cached)
        if cached is not None and self._is_fresh_as_of(freshness_anchor):
            return self._decorate_overview_response(cached, build_status="fresh_cache")

        if cached is not None:
            self._schedule_overview_refresh()
            return self._decorate_overview_response(cached, build_status="stale_cache")

        live = await self._await_overview_live()
        if self._overview_has_truth(live):
            self._store_overview_cache(live)
            return self._decorate_overview_response(live, build_status="live")

        return self._decorate_overview_response(live, build_status="degraded_live")

    async def get_overview_debug(self) -> dict:
        started = time.perf_counter()

        (
            positions_payload,
            dashboard_payload,
            runtime_payload,
            registry_payload,
        ) = await asyncio.gather(
            self.v12_client.get_portfolio_positions(),
            self.v12_client.get_portfolio_dashboard(),
            self.v12_client.get_runtime_status(),
            self.v12_client.get_strategy_registry(),
        )

        portfolio_positions = self._as_dict(positions_payload)
        portfolio_dashboard = self._as_dict(dashboard_payload)
        portfolio = portfolio_positions if portfolio_positions else portfolio_dashboard
        runtime = self._as_dict(runtime_payload)
        registry = self._as_dict(registry_payload)
        summary = (
            portfolio_dashboard.get("summary")
            if isinstance(portfolio_dashboard.get("summary"), dict)
            else portfolio_dashboard
        )
        summary = summary if isinstance(summary, dict) else {}
        summary_total_equity = self._safe_float(
            summary.get("total_equity") or summary.get("portfolio_value") or 0.0
        )
        summary_total_equity = self._safe_float(
            summary.get("total_equity") or summary.get("portfolio_value") or 0.0
        )

        items = portfolio.get("items") or portfolio.get("positions") or []
        if not isinstance(items, list):
            items = []

        weights: list[float] = []
        total_pnl = 0.0
        used_margin_from_positions = 0.0
        unrealized_from_positions = 0.0
        market_value_from_positions = 0.0
        valid_positions: list[dict] = []

        for row in items:
            if not isinstance(row, dict):
                continue
            valid_positions.append(row)
            weight = self._safe_float(row.get("weight", row.get("target_weight", 0.0)))
            side = str(row.get("side", "long") or "long").lower()
            if weight == 0.0 and summary_total_equity > 0.0:
                notional = self._safe_float(
                    row.get("exposure_notional", row.get("notional_usd", row.get("notional", 0.0)))
                )
                weight = notional / max(abs(summary_total_equity), 1e-9)
            if side == "short" and weight > 0:
                weight = -weight
            weights.append(weight)
            pnl = self._safe_float(row.get("pnl", row.get("unrealized_pnl", 0.0)))
            total_pnl += pnl
            signed_qty = self._safe_float(
                row.get("signed_qty", row.get("quantity", row.get("qty", row.get("position_qty", 0.0))))
            )
            avg_price = abs(self._safe_float(row.get("avg_price", row.get("avg_entry_price", row.get("avg", 0.0)))))
            mark_price = self._safe_float(row.get("mark_price", row.get("markPrice", row.get("price", row.get("last_price", avg_price)))))
            used_margin_from_positions += abs(signed_qty) * avg_price
            unrealized_from_positions += pnl
            market_value_from_positions += signed_qty * mark_price

        breakdown_failed = False
        try:
            breakdown = compute_equity_breakdown(portfolio_dashboard, portfolio)
        except Exception:
            breakdown_failed = True
            logger.exception("equity_breakdown_failed_dashboard_debug")
            summary_balance = self._safe_float(
                summary.get("cash_balance")
                or summary.get("balance")
                or summary.get("cash")
                or summary.get("free_cash")
                or 0.0
            )
            summary_used_margin = self._safe_float(summary.get("used_margin") or 0.0)
            summary_unrealized = self._safe_float(summary.get("unrealized_pnl") or summary.get("unrealized") or 0.0)
            summary_total_equity = self._safe_float(
                summary.get("total_equity")
                or summary.get("portfolio_value")
                or (summary_balance + self._safe_float(summary.get("market_value") or 0.0))
                or 0.0
            )
            breakdown = {
                "balance": round(summary_balance, 2),
                "used_margin": round(summary_used_margin, 2),
                "free_margin": round(summary_total_equity - summary_used_margin, 2),
                "unrealized": round(summary_unrealized, 2),
                "total_equity": round(summary_total_equity, 2),
            }

        total_equity = self._safe_float(breakdown.get("total_equity"))
        balance = self._safe_float(breakdown.get("balance"))
        used_margin = self._safe_float(breakdown.get("used_margin"))
        free_margin = self._safe_float(breakdown.get("free_margin"))
        unrealized = self._safe_float(breakdown.get("unrealized"))

        gross_exposure = self._safe_float(summary.get("gross_exposure", summary.get("grossExposure", 0.0)))
        net_exposure = self._safe_float(summary.get("net_exposure", summary.get("netExposure", 0.0)))
        gross_exposure_source = "dashboard.summary.gross_exposure"
        net_exposure_source = "dashboard.summary.net_exposure"
        if gross_exposure == 0.0 and weights:
            gross_exposure = sum(abs(v) for v in weights)
            gross_exposure_source = "derived(sum(abs(position.weight)))"
        if net_exposure == 0.0 and weights:
            net_exposure = sum(weights)
            net_exposure_source = "derived(sum(position.weight))"

        realized_pnl = self._safe_float(summary.get("realized_pnl", 0.0))
        unrealized_pnl_summary = self._safe_float(summary.get("unrealized_pnl", 0.0))
        pnl = realized_pnl + unrealized_pnl_summary
        pnl_source = "dashboard.summary.realized_pnl + dashboard.summary.unrealized_pnl"
        if pnl == 0.0:
            pnl = total_pnl
            pnl_source = "derived(sum(position.pnl))"

        active_strategies = int(
            registry.get("enabled_count")
            or len(registry.get("strategies") or [])
            or len(valid_positions)
        )

        try:
            job_rows = self.scheduler_repository.list_jobs()
        except Exception:
            logger.exception("dashboard_scheduler_jobs_failed_debug")
            job_rows = []

        running_jobs = sum(
            1
            for row in job_rows
            if str((row or {}).get("status", "idle")).lower() in {"running", "active"}
        )

        try:
            alerts_payload = self.alert_service.list_alerts()
        except Exception:
            logger.exception("dashboard_alerts_read_failed_debug")
            alerts_payload = {"items": [], "count": 0, "open_count": 0}

        alerts = alerts_payload.get("items") or []
        open_alert_count = int(alerts_payload.get("open_count", alerts_payload.get("count", 0)) or 0)
        as_of = runtime.get("as_of") or portfolio_dashboard.get("as_of") or portfolio.get("as_of") or utc_now_iso()

        balance_key = self._first_present_key(summary, "balance", "cash_balance", "cash", "free_cash")
        total_equity_key = self._first_present_key(summary, "total_equity", "portfolio_value")
        used_margin_key = self._first_present_key(summary, "used_margin")
        unrealized_key = self._first_present_key(summary, "unrealized_pnl", "unrealized")

        field_sources = {
            "total_equity": (
                f"dashboard.summary.{total_equity_key}"
                if total_equity_key
                else "derived(balance + positions.market_value)"
                if valid_positions
                else "derived(balance + summary.market_value)"
            ),
            "balance": f"dashboard.summary.{balance_key}" if balance_key else "derived(default_zero)",
            "used_margin": (
                "derived(sum(abs(position.signed_qty) * position.avg_price))"
                if valid_positions
                else f"dashboard.summary.{used_margin_key}"
                if used_margin_key
                else "derived(default_zero)"
            ),
            "free_margin": "derived(total_equity - used_margin)",
            "unrealized": (
                "derived(sum(position.pnl))"
                if valid_positions
                else f"dashboard.summary.{unrealized_key}"
                if unrealized_key
                else "derived(default_zero)"
            ),
            "daily_pnl": pnl_source,
            "gross_exposure": gross_exposure_source,
            "net_exposure": net_exposure_source,
        }

        degraded_inputs = [
            name
            for name, payload in {
                "portfolio_positions": portfolio,
                "portfolio_dashboard": portfolio_dashboard,
                "runtime_status": runtime,
                "strategy_registry": registry,
            }.items()
            if str(payload.get("status", "") or "").lower() == "degraded"
        ]

        status = "ok"
        source = "live"
        reason = None
        if degraded_inputs:
            status = "fallback"
            reason = "degraded_upstream_payload"
            if any(str(value).startswith("derived(") for value in field_sources.values()):
                source = "derived"

        duration_ms = round((time.perf_counter() - started) * 1000.0, 2)
        return {
            "scope": "dashboard.overview",
            "status": status,
            "source": source,
            "reason": reason,
            "as_of": as_of,
            "timings": {
                "handler_ms": duration_ms,
                "snapshot_age_sec": self._snapshot_age_sec(as_of),
            },
            "summary": {
                "total_equity": round(total_equity, 2),
                "balance": round(balance, 2),
                "used_margin": round(used_margin, 2),
                "free_margin": round(free_margin, 2),
                "unrealized": round(unrealized, 2),
                "daily_pnl": round(pnl, 6),
                "gross_exposure": round(gross_exposure, 6),
                "net_exposure": round(net_exposure, 6),
                "active_strategies": active_strategies,
                "open_alerts": open_alert_count,
                "running_jobs": running_jobs,
            },
            "provenance": {
                "read_mode": "live_aggregate_with_truth_fields",
                "background_refresh_scheduled": False,
                "upstream_dependencies": [
                    "v12:/portfolio/positions/latest",
                    "v12:/portfolio/overview",
                    "v12:/runtime/status",
                    "v12:/strategy/registry",
                ],
                "field_sources": field_sources,
                "degraded_inputs": degraded_inputs,
                "breakdown_failed": breakdown_failed,
            },
            "counts": {
                "position_count": len(valid_positions),
                "alert_count": len(alerts) if isinstance(alerts, list) else 0,
                "job_count": len(job_rows),
            },
            "raw": {
                "portfolio_positions": portfolio_positions,
                "portfolio_dashboard": portfolio_dashboard,
                "runtime_status": runtime,
                "strategy_registry": registry,
                "computed": {
                    "weights": weights,
                    "used_margin_from_positions": round(used_margin_from_positions, 6),
                    "unrealized_from_positions": round(unrealized_from_positions, 6),
                    "market_value_from_positions": round(market_value_from_positions, 6),
                },
            },
        }

    async def get_system_health(self) -> dict:
        payload = await self.v12_client.get_system_health()
        runtime = await self.v12_client.get_runtime_status()
        services = payload.get("services")
        if not isinstance(services, dict):
            services = {
                "api": "ok" if payload.get("status") == "ok" else "unknown",
                "runtime": payload.get("mode", "unknown"),
                "phase": payload.get("phase"),
                "sprint": payload.get("sprint"),
            }
        services.setdefault("paper_runtime", "ok" if runtime.get("latest_run_id") else "idle")
        return {
            "status": payload.get("status", "unknown"),
            "services": services,
            "as_of": runtime.get("as_of") or payload.get("as_of") or utc_now_iso(),
        }

    def get_job_status(self) -> dict:
        return {"jobs": self.scheduler_repository.list_jobs()}
