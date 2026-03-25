from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
import logging

from app.clients.v12_client import V12Client, utc_now_iso
from app.services.equity_breakdown import compute_equity_breakdown


logger = logging.getLogger(__name__)


class PortfolioService:
    OVERVIEW_CACHE_TTL_SECONDS = 5.0
    OVERVIEW_STALE_MAX_AGE_SECONDS = 60.0
    POSITIONS_CACHE_TTL_SECONDS = 5.0
    POSITIONS_STALE_MAX_AGE_SECONDS = 60.0
    METRICS_CACHE_TTL_SECONDS = 5.0
    METRICS_STALE_MAX_AGE_SECONDS = 60.0
    METRICS_EQUITY_HISTORY_LIMIT = 60

    def __init__(self, v12_client: V12Client) -> None:
        self.v12_client = v12_client
        self._overview_cache: dict | None = None
        self._overview_cache_expires_at: datetime | None = None
        self._overview_cache_updated_at: datetime | None = None
        self._overview_inflight_task: asyncio.Task | None = None
        self._positions_cache: dict | None = None
        self._positions_cache_expires_at: datetime | None = None
        self._positions_cache_updated_at: datetime | None = None
        self._positions_inflight_task: asyncio.Task | None = None
        self._metrics_cache: dict | None = None
        self._metrics_cache_expires_at: datetime | None = None
        self._metrics_cache_updated_at: datetime | None = None
        self._metrics_inflight_task: asyncio.Task | None = None

    @staticmethod
    def _safe_float(value: object, default: float = 0.0) -> float:
        try:
            if value is None:
                return default
            return float(value)
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

    @staticmethod
    def _parse_iso_timestamp(value: object) -> datetime | None:
        if not value:
            return None
        try:
            ts = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
            if ts.tzinfo is None:
                return ts.replace(tzinfo=timezone.utc)
            return ts.astimezone(timezone.utc)
        except Exception:
            return None

    @staticmethod
    def _first_present_key(payload: dict, *keys: str) -> str | None:
        for key in keys:
            if key in payload and payload.get(key) is not None:
                return key
        return None

    @staticmethod
    def _safe_expected_sharpe_from_equity_history(items: list[dict]) -> float | None:
        if len(items) < 3:
            return 0.0 if items else None
        returns: list[float] = []
        prev = None
        for item in items:
            value = float(item.get("value", 0.0) or 0.0)
            if prev and abs(prev) > 1e-9:
                returns.append((value - prev) / abs(prev))
            prev = value
        if len(returns) < 2:
            return 0.0
        mean_ret = sum(returns) / len(returns)
        variance = sum((r - mean_ret) ** 2 for r in returns) / max(len(returns) - 1, 1)
        std = variance ** 0.5
        if std < 1e-6:
            return 0.0
        sharpe = mean_ret / std
        return round(max(-10.0, min(10.0, sharpe)), 6)

    @staticmethod
    def _decorate_overview_contract(payload: dict, *, build_status: str) -> dict:
        result = dict(payload)
        result['rebuilt_at'] = result.get('rebuilt_at') or utc_now_iso()
        result['build_status'] = build_status
        stable_value = {
            'total_equity': result.get('total_equity'),
            'balance': result.get('balance'),
            'used_margin': result.get('used_margin'),
            'free_margin': result.get('free_margin'),
            'unrealized': result.get('unrealized'),
            'gross_exposure': result.get('gross_exposure'),
            'net_exposure': result.get('net_exposure'),
            'realized_pnl': result.get('realized_pnl'),
            'unrealized_pnl': result.get('unrealized_pnl'),
        }
        result['stable_value'] = stable_value
        result['live_delta'] = {
            'positions_window': None,
            'metrics_window': None,
        }
        result['display_value'] = dict(stable_value)
        return result

    @staticmethod
    def _decorate_metrics_contract(payload: dict, *, build_status: str) -> dict:
        result = dict(payload)
        result['rebuilt_at'] = result.get('rebuilt_at') or utc_now_iso()
        result['build_status'] = build_status
        stable_value = {
            'fill_rate': result.get('fill_rate'),
            'expected_sharpe': result.get('expected_sharpe'),
            'expected_volatility': result.get('expected_volatility'),
        }
        result['stable_value'] = stable_value
        result['live_delta'] = {
            'recent_fills_window': None,
            'recent_equity_points_window': None,
        }
        result['display_value'] = dict(stable_value)
        return result

    def _decorate_cached_overview_response(self, payload: dict, *, build_status: str) -> dict:
        return self._decorate_overview_contract(payload, build_status=build_status)

    def _decorate_cached_metrics_response(self, payload: dict, *, build_status: str) -> dict:
        return self._decorate_metrics_contract(payload, build_status=build_status)

    def _get_cached_metrics(self, *, allow_stale: bool = False) -> dict | None:
        expires_at = self._metrics_cache_expires_at
        updated_at = self._metrics_cache_updated_at
        if self._metrics_cache is None or expires_at is None or updated_at is None:
            return None
        now = datetime.now(timezone.utc)
        if expires_at > now:
            return dict(self._metrics_cache)
        if not allow_stale:
            return None
        if (now - updated_at).total_seconds() > self.METRICS_STALE_MAX_AGE_SECONDS:
            return None
        return dict(self._metrics_cache)

    def _get_cached_overview(self, *, allow_stale: bool = False) -> dict | None:
        expires_at = self._overview_cache_expires_at
        updated_at = self._overview_cache_updated_at
        if self._overview_cache is None or expires_at is None or updated_at is None:
            return None
        now = datetime.now(timezone.utc)
        if expires_at > now:
            return dict(self._overview_cache)
        if not allow_stale:
            return None
        if (now - updated_at).total_seconds() > self.OVERVIEW_STALE_MAX_AGE_SECONDS:
            return None
        return dict(self._overview_cache)

    def _get_cached_positions(self, *, allow_stale: bool = False) -> dict | None:
        expires_at = self._positions_cache_expires_at
        updated_at = self._positions_cache_updated_at
        if self._positions_cache is None or expires_at is None or updated_at is None:
            return None
        now = datetime.now(timezone.utc)
        if expires_at > now:
            return dict(self._positions_cache)
        if not allow_stale:
            return None
        if (now - updated_at).total_seconds() > self.POSITIONS_STALE_MAX_AGE_SECONDS:
            return None
        return dict(self._positions_cache)

    async def _build_metrics_live(self) -> dict:
        metrics_payload = await self.v12_client.get_portfolio_metrics()
        metrics_payload = metrics_payload if isinstance(metrics_payload, dict) else {}
        if metrics_payload.get("status") not in {"degraded", "missing", "unsupported"} and (
            "fill_rate" in metrics_payload or "expected_sharpe" in metrics_payload
        ):
            payload = {
                "fill_rate": self._safe_float(metrics_payload.get("fill_rate"), 0.0),
                "expected_sharpe": (
                    None if metrics_payload.get("expected_sharpe") is None
                    else self._safe_float(metrics_payload.get("expected_sharpe"), 0.0)
                ),
                "expected_volatility": self._safe_float(metrics_payload.get("expected_volatility"), 0.0),
                "as_of": metrics_payload.get("as_of") or metrics_payload.get("source_snapshot_time") or utc_now_iso(),
                "source_snapshot_time": metrics_payload.get("source_snapshot_time"),
                "build_status": metrics_payload.get("build_status"),
            }
            self._metrics_cache = dict(payload)
            now = datetime.now(timezone.utc)
            self._metrics_cache_updated_at = now
            self._metrics_cache_expires_at = now + timedelta(seconds=self.METRICS_CACHE_TTL_SECONDS)
            return payload

        execution_quality, equity_history = await asyncio.gather(
            self.v12_client.get_execution_quality(),
            self.v12_client.get_equity_history(limit=self.METRICS_EQUITY_HISTORY_LIMIT),
        )
        execution_quality = execution_quality if isinstance(execution_quality, dict) else {}
        equity_history = equity_history if isinstance(equity_history, dict) else {}
        equity_items = equity_history.get("items") or []
        if not isinstance(equity_items, list):
            equity_items = []

        returns: list[float] = []
        prev = None
        for item in equity_items:
            value = self._safe_float(item.get("value"))
            if prev and abs(prev) > 1e-9:
                returns.append((value - prev) / abs(prev))
            prev = value

        expected_volatility = 0.0
        if returns:
            mean_ret = sum(returns) / len(returns)
            variance = sum((r - mean_ret) ** 2 for r in returns) / max(len(returns) - 1, 1)
            expected_volatility = round(variance ** 0.5, 6)

        payload = {
            "fill_rate": self._safe_float(execution_quality.get("fill_rate"), 0.0),
            "expected_sharpe": self._safe_expected_sharpe_from_equity_history(equity_items),
            "expected_volatility": expected_volatility,
            "as_of": execution_quality.get("as_of") or equity_history.get("as_of") or utc_now_iso(),
            "source_snapshot_time": execution_quality.get("as_of") or equity_history.get("as_of"),
            "build_status": "live_fallback",
        }
        self._metrics_cache = dict(payload)
        now = datetime.now(timezone.utc)
        self._metrics_cache_updated_at = now
        self._metrics_cache_expires_at = now + timedelta(seconds=self.METRICS_CACHE_TTL_SECONDS)
        return payload

    def _schedule_metrics_refresh(self) -> None:
        task = self._metrics_inflight_task
        if task is not None and not task.done():
            return
        self._metrics_inflight_task = asyncio.create_task(self._build_metrics_live())

        def _clear_task(finished: asyncio.Task) -> None:
            try:
                finished.exception()
            except Exception:
                logger.exception("portfolio_metrics_background_refresh_failed")
            finally:
                if self._metrics_inflight_task is finished:
                    self._metrics_inflight_task = None

        self._metrics_inflight_task.add_done_callback(_clear_task)

    async def _build_overview_live(self) -> dict:
        overview_payload, positions_payload = await asyncio.gather(
            self.v12_client.get_portfolio_dashboard(),
            self.get_positions(),
        )
        overview = overview_payload if isinstance(overview_payload, dict) else {}
        positions_response = positions_payload if isinstance(positions_payload, dict) else {}
        positions_source = overview
        positions = positions_response.get("items") if isinstance(positions_response.get("items"), list) else []
        if not positions:
            positions = self._normalize_positions(positions_source)
        positions_breakdown_payload = {"items": positions}
        summary = overview.get('summary') if isinstance(overview.get('summary'), dict) else overview
        try:
            breakdown = compute_equity_breakdown(overview, positions_breakdown_payload)
        except Exception:  # pragma: no cover - defensive fallback for malformed upstream payloads
            logger.exception('equity_breakdown_failed_portfolio')
            summary_balance = float(summary.get('cash_balance', 0.0) or summary.get('balance', 0.0) or summary.get('cash', 0.0) or summary.get('free_cash', 0.0) or 0.0)
            summary_used_margin = float(summary.get('used_margin', 0.0) or 0.0)
            summary_unrealized = float(summary.get('unrealized_pnl', 0.0) or summary.get('unrealized', 0.0) or 0.0)
            summary_total_equity = float(
                summary.get('total_equity', 0.0)
                or summary.get('portfolio_value', 0.0)
                or (summary_balance + float(summary.get('market_value', 0.0) or 0.0))
                or 0.0
            )
            breakdown = {
                'balance': round(summary_balance, 2),
                'used_margin': round(summary_used_margin, 2),
                'free_margin': round(summary_total_equity - summary_used_margin, 2),
                'unrealized': round(summary_unrealized, 2),
                'total_equity': round(summary_total_equity, 2),
            }
        total_equity = float(breakdown['total_equity'] or 0.0)
        gross_exposure = float(summary.get('gross_exposure', 0.0) or 0.0)
        net_exposure = float(summary.get('net_exposure', 0.0) or 0.0)
        realized_pnl = float(summary.get('realized_pnl', 0.0) or 0.0)
        unrealized_pnl = float(summary.get('unrealized_pnl', 0.0) or 0.0)
        pnl = round(realized_pnl + unrealized_pnl, 6)
        expected_volatility = round(max(gross_exposure * 0.08, 0.0), 6)
        long_exposure = float(summary.get('long_exposure', 0.0) or 0.0)
        short_exposure = float(summary.get('short_exposure', 0.0) or 0.0)
        if positions and long_exposure == 0.0 and short_exposure == 0.0:
            long_exposure = sum(max(0.0, float(item.get('weight', 0.0) or 0.0)) for item in positions)
            short_exposure = sum(abs(min(0.0, float(item.get('weight', 0.0) or 0.0))) for item in positions)
        payload = {
            'portfolio_value': round(total_equity, 2),
            'total_equity': round(total_equity, 2),
            'balance': breakdown['balance'],
            'cash': breakdown['balance'],
            'cash_balance': breakdown['balance'],
            'free_cash': breakdown['free_margin'],
            'free_margin': breakdown['free_margin'],
            'used_margin': breakdown['used_margin'],
            'unrealized': breakdown['unrealized'],
            'collateral_equity': breakdown['total_equity'],
            'available_margin': breakdown['free_margin'],
            'margin_utilization': float(summary.get('margin_utilization', gross_exposure) or gross_exposure),
            'pnl': pnl,
            'realized_pnl': realized_pnl,
            'unrealized_pnl': breakdown['unrealized'],
            'fees_paid': float(summary.get('fees_paid', 0.0) or 0.0),
            'drawdown': float(summary.get('drawdown', 0.0) or 0.0),
            'gross_exposure': round(gross_exposure, 6),
            'net_exposure': round(net_exposure, 6),
            'long_exposure': round(long_exposure, 6),
            'short_exposure': round(short_exposure, 6),
            'leverage': round(gross_exposure, 6),
            'expected_volatility': expected_volatility,
            'weights': {item['symbol']: item['weight'] for item in positions},
            'positions': positions,
            'quotes_as_of': overview.get('quotes_as_of') or positions_source.get('quotes_as_of'),
            'stale_positions': sum(1 for item in positions if bool(item.get('stale'))),
            'source_snapshot_time': overview.get('source_snapshot_time') or overview.get('as_of') or positions_source.get('as_of'),
            'as_of': overview.get('as_of') or positions_source.get('as_of') or utc_now_iso(),
            'build_status': overview.get('build_status') or 'live',
        }
        self._overview_cache = dict(payload)
        now = datetime.now(timezone.utc)
        self._overview_cache_updated_at = now
        self._overview_cache_expires_at = now + timedelta(seconds=self.OVERVIEW_CACHE_TTL_SECONDS)
        return payload

    def _schedule_overview_refresh(self) -> None:
        task = self._overview_inflight_task
        if task is not None and not task.done():
            return
        self._overview_inflight_task = asyncio.create_task(self._build_overview_live())

        def _clear_task(finished: asyncio.Task) -> None:
            try:
                finished.exception()
            except Exception:
                logger.exception("portfolio_overview_background_refresh_failed")
            finally:
                if self._overview_inflight_task is finished:
                    self._overview_inflight_task = None

        self._overview_inflight_task.add_done_callback(_clear_task)

    async def _build_positions_live(self) -> dict:
        payload = await self.v12_client.get_portfolio_positions()
        payload = payload if isinstance(payload, dict) else {}
        positions = self._normalize_positions(payload)
        result = {
            "items": positions,
            "as_of": payload.get("as_of") or utc_now_iso(),
            "source_snapshot_time": payload.get("source_snapshot_time") or payload.get("as_of"),
            "rebuilt_at": payload.get("rebuilt_at") or utc_now_iso(),
            "build_status": payload.get("build_status") or "live",
        }
        snapshot_age = self._snapshot_age_sec(result.get("source_snapshot_time"))
        if snapshot_age is not None:
            result["data_freshness_sec"] = snapshot_age
        self._positions_cache = dict(result)
        now = datetime.now(timezone.utc)
        self._positions_cache_updated_at = now
        self._positions_cache_expires_at = now + timedelta(seconds=self.POSITIONS_CACHE_TTL_SECONDS)
        return result

    def _schedule_positions_refresh(self) -> None:
        task = self._positions_inflight_task
        if task is not None and not task.done():
            return
        self._positions_inflight_task = asyncio.create_task(self._build_positions_live())

        def _clear_task(finished: asyncio.Task) -> None:
            try:
                finished.exception()
            except Exception:
                logger.exception("portfolio_positions_background_refresh_failed")
            finally:
                if self._positions_inflight_task is finished:
                    self._positions_inflight_task = None

        self._positions_inflight_task.add_done_callback(_clear_task)

    async def get_overview(self) -> dict:
        cached = self._get_cached_overview()
        if cached is not None:
            return self._decorate_cached_overview_response(cached, build_status='fresh_cache')

        stale_cached = self._get_cached_overview(allow_stale=True)
        if stale_cached is not None:
            self._schedule_overview_refresh()
            return self._decorate_cached_overview_response(stale_cached, build_status='stale_cache')

        task = self._overview_inflight_task
        if task is not None and not task.done():
            return await task

        task = asyncio.create_task(self._build_overview_live())
        self._overview_inflight_task = task
        try:
            return self._decorate_cached_overview_response(await task, build_status='live')
        finally:
            if self._overview_inflight_task is task:
                self._overview_inflight_task = None

    async def get_metrics(self) -> dict:
        cached = self._get_cached_metrics()
        if cached is not None:
            return self._decorate_cached_metrics_response(cached, build_status='fresh_cache')

        stale_cached = self._get_cached_metrics(allow_stale=True)
        if stale_cached is not None:
            self._schedule_metrics_refresh()
            return self._decorate_cached_metrics_response(stale_cached, build_status='stale_cache')

        task = self._metrics_inflight_task
        if task is not None and not task.done():
            return await task

        task = asyncio.create_task(self._build_metrics_live())
        self._metrics_inflight_task = task
        try:
            return self._decorate_cached_metrics_response(await task, build_status='live')
        finally:
            if self._metrics_inflight_task is task:
                self._metrics_inflight_task = None

    async def get_positions(self) -> dict:
        cached = self._get_cached_positions()
        if cached is not None:
            return cached

        stale_cached = self._get_cached_positions(allow_stale=True)
        if stale_cached is not None:
            self._schedule_positions_refresh()
            return stale_cached

        task = self._positions_inflight_task
        if task is not None and not task.done():
            return await task

        task = asyncio.create_task(self._build_positions_live())
        self._positions_inflight_task = task
        try:
            return await task
        finally:
            if self._positions_inflight_task is task:
                self._positions_inflight_task = None

    async def get_positions_debug(self) -> dict:
        payload = await self.v12_client.get_portfolio_positions()
        payload = payload if isinstance(payload, dict) else {}
        positions = self._normalize_positions(payload, include_debug_fields=True)
        raw_positions = payload.get("items") or payload.get("positions") or []
        if not isinstance(raw_positions, list):
            raw_positions = []

        field_sources = []
        stale_count = 0
        for index, row in enumerate(raw_positions):
            if not isinstance(row, dict):
                continue
            position = positions[index] if index < len(positions) else {}
            if bool(position.get("stale")):
                stale_count += 1
            field_sources.append(
                {
                    "symbol": position.get("symbol", row.get("symbol", "unknown")),
                    "sources": {
                        "quantity": "quantity|qty|position_qty",
                        "avg_price": "avg_price|avg_entry_price|avg",
                        "mark_price": "mark_price|markPrice|price|last_price",
                        "pnl": "pnl|unrealized_pnl",
                        "weight": "weight|target_weight",
                        "strategy_id": "strategy_id|run_id|payload.run_id",
                    },
                }
            )

        status = "ok"
        source = "live"
        reason = None
        if str(payload.get("status", "") or "").lower() == "degraded":
            status = "fallback"
            source = "derived"
            reason = "degraded_upstream_payload"
        elif not positions:
            status = "no_data"
            source = "empty"
            reason = "positions_unavailable"

        as_of = payload.get("as_of") or utc_now_iso()
        return {
            "scope": "portfolio.positions",
            "status": status,
            "source": source,
            "reason": reason,
            "as_of": as_of,
            "timings": {
                "snapshot_age_sec": self._snapshot_age_sec(as_of),
            },
            "summary": {
                "position_count": len(positions),
                "gross_exposure": round(sum(abs(float(item.get("weight", 0.0) or 0.0)) for item in positions), 6),
                "net_exposure": round(sum(float(item.get("weight", 0.0) or 0.0) for item in positions), 6),
                "stale_positions": stale_count,
            },
            "provenance": {
                "read_mode": "normalized_positions",
                "background_refresh_scheduled": False,
                "upstream_dependencies": ["v12:/portfolio/positions/latest"],
                "field_sources": field_sources,
            },
            "counts": {
                "position_count": len(positions),
                "stale_positions": stale_count,
            },
            "raw": {
                "positions_payload": payload,
                "normalized_positions": positions,
            },
        }

    async def get_exposure(self) -> dict:
        positions = await self.get_positions()
        gross_exposure = sum(abs(float(item.get('weight', 0.0) or 0.0)) for item in positions)
        net_exposure = sum(float(item.get('weight', 0.0) or 0.0) for item in positions)
        return {
            'gross_exposure': round(gross_exposure, 6),
            'net_exposure': round(net_exposure, 6),
            'long_exposure': round(sum(max(0.0, float(item.get('weight', 0.0) or 0.0)) for item in positions), 6),
            'short_exposure': round(sum(abs(min(0.0, float(item.get('weight', 0.0) or 0.0))) for item in positions), 6),
            'leverage': round(gross_exposure, 6),
            'as_of': utc_now_iso(),
        }

    async def get_overview_debug(self) -> dict:
        overview_payload, positions_payload = await asyncio.gather(
            self.v12_client.get_portfolio_dashboard(),
            self.v12_client.get_portfolio_positions(),
        )
        overview = overview_payload if isinstance(overview_payload, dict) else {}
        positions_source = positions_payload if isinstance(positions_payload, dict) else {}
        if not positions_source:
            positions_source = overview
        positions = self._normalize_positions(positions_source, include_debug_fields=True)
        summary = overview.get("summary") if isinstance(overview.get("summary"), dict) else overview
        summary = summary if isinstance(summary, dict) else {}

        breakdown_failed = False
        try:
            breakdown = compute_equity_breakdown(overview, positions_source)
        except Exception:
            breakdown_failed = True
            logger.exception("equity_breakdown_failed_portfolio_debug")
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
        gross_exposure = self._safe_float(summary.get("gross_exposure", 0.0))
        net_exposure = self._safe_float(summary.get("net_exposure", 0.0))
        long_exposure = self._safe_float(summary.get("long_exposure", 0.0))
        short_exposure = self._safe_float(summary.get("short_exposure", 0.0))
        if positions and long_exposure == 0.0 and short_exposure == 0.0:
            long_exposure = sum(max(0.0, float(item.get("weight", 0.0) or 0.0)) for item in positions)
            short_exposure = sum(abs(min(0.0, float(item.get("weight", 0.0) or 0.0))) for item in positions)
        if gross_exposure == 0.0 and positions:
            gross_exposure = sum(abs(float(item.get("weight", 0.0) or 0.0)) for item in positions)
        if net_exposure == 0.0 and positions:
            net_exposure = sum(float(item.get("weight", 0.0) or 0.0) for item in positions)

        realized_pnl = self._safe_float(summary.get("realized_pnl", 0.0))
        unrealized_pnl = self._safe_float(summary.get("unrealized_pnl", 0.0))
        pnl = round(realized_pnl + unrealized_pnl, 6)
        if pnl == 0.0:
            pnl = round(sum(self._safe_float(item.get("pnl", 0.0)) for item in positions), 6)

        balance_key = self._first_present_key(summary, "balance", "cash_balance", "cash", "free_cash")
        total_equity_key = self._first_present_key(summary, "total_equity", "portfolio_value")
        used_margin_key = self._first_present_key(summary, "used_margin")
        unrealized_key = self._first_present_key(summary, "unrealized_pnl", "unrealized")
        market_value_key = self._first_present_key(summary, "market_value")
        quotes_as_of = overview.get("quotes_as_of") or positions_source.get("quotes_as_of")
        as_of = overview.get("as_of") or positions_source.get("as_of") or utc_now_iso()
        status = "ok"
        source = "live"
        reason = None
        degraded_inputs = [
            name
            for name, payload in {
                "portfolio_dashboard": overview,
            }.items()
            if str(payload.get("status", "") or "").lower() == "degraded"
        ]
        if degraded_inputs:
            status = "fallback"
            source = "derived"
            reason = "degraded_upstream_payload"
        elif total_equity == 0.0 and balance == 0.0 and not positions:
            status = "no_data"
            source = "empty"
            reason = "portfolio_overview_unavailable"

        market_value_from_positions = round(
            sum(self._safe_float(item.get("quantity", 0.0)) * self._safe_float(item.get("mark_price", 0.0)) for item in positions),
            6,
        )
        equity_trace = {
            "balance": round(balance, 2),
            "market_value": round(self._safe_float(summary.get("market_value", market_value_from_positions)), 2),
            "market_value_source": f"summary.{market_value_key}" if market_value_key else "derived(sum(position.quantity * position.mark_price))",
            "used_margin": round(used_margin, 2),
            "unrealized": round(unrealized, 2),
            "total_equity": round(total_equity, 2),
            "formula": "total_equity = balance + market_value",
        }

        return {
            "scope": "portfolio.overview",
            "status": status,
            "source": source,
            "reason": reason,
            "as_of": as_of,
            "timings": {
                "snapshot_age_sec": self._snapshot_age_sec(as_of),
                "quotes_age_sec": self._snapshot_age_sec(quotes_as_of) if quotes_as_of else None,
            },
            "summary": {
                "total_equity": round(total_equity, 2),
                "balance": round(balance, 2),
                "used_margin": round(used_margin, 2),
                "free_margin": round(free_margin, 2),
                "unrealized": round(unrealized, 2),
                "realized_pnl": round(realized_pnl, 6),
                "daily_pnl": pnl,
                "gross_exposure": round(gross_exposure, 6),
                "net_exposure": round(net_exposure, 6),
                "long_exposure": round(long_exposure, 6),
                "short_exposure": round(short_exposure, 6),
            },
            "provenance": {
                "read_mode": "portfolio_overview_with_equity_trace",
                "background_refresh_scheduled": False,
                "upstream_dependencies": [
                    "v12:/portfolio/overview",
                    "v12:/portfolio/positions/latest",
                ],
                "field_sources": {
                    "total_equity": f"summary.{total_equity_key}" if total_equity_key else "derived(balance + market_value)",
                    "balance": f"summary.{balance_key}" if balance_key else "derived(default_zero)",
                    "used_margin": "derived(sum(abs(position.quantity) * position.avg_price))" if positions else f"summary.{used_margin_key}" if used_margin_key else "derived(default_zero)",
                    "free_margin": "derived(total_equity - used_margin)",
                    "unrealized": "derived(sum(position.pnl))" if positions else f"summary.{unrealized_key}" if unrealized_key else "derived(default_zero)",
                    "gross_exposure": "summary.gross_exposure" if summary.get("gross_exposure") not in (None, 0.0) else "derived(sum(abs(position.weight)))",
                    "net_exposure": "summary.net_exposure" if summary.get("net_exposure") not in (None, 0.0) else "derived(sum(position.weight))",
                    "long_exposure": "summary.long_exposure" if summary.get("long_exposure") not in (None, 0.0) else "derived(sum(max(position.weight, 0)))",
                    "short_exposure": "summary.short_exposure" if summary.get("short_exposure") not in (None, 0.0) else "derived(sum(abs(min(position.weight, 0))))",
                },
                "degraded_inputs": degraded_inputs,
                "breakdown_failed": breakdown_failed,
                "equity_trace": equity_trace,
            },
            "counts": {
                "position_count": len(positions),
                "stale_positions": sum(1 for item in positions if bool(item.get("stale"))),
            },
            "raw": {
                "portfolio_dashboard": overview,
                "portfolio_positions": positions_source,
                "normalized_positions": positions,
            },
        }

    async def get_metrics_debug(self) -> dict:
        execution_quality, equity_history = await asyncio.gather(
            self.v12_client.get_execution_quality(live=True),
            self.v12_client.get_equity_history(limit=self.METRICS_EQUITY_HISTORY_LIMIT, live=True),
        )
        execution_quality = execution_quality if isinstance(execution_quality, dict) else {}
        equity_history = equity_history if isinstance(equity_history, dict) else {}
        metrics = await self.get_metrics()
        equity_points = equity_history.get("items") or []
        if not isinstance(equity_points, list):
            equity_points = []

        return {
            "scope": "portfolio.metrics",
            "status": "ok",
            "source": "live",
            "reason": None,
            "as_of": metrics["as_of"],
            "timings": {
                "snapshot_age_sec": self._snapshot_age_sec(metrics["as_of"]),
            },
            "summary": metrics,
            "provenance": {
                "read_mode": "metrics_only",
                "background_refresh_scheduled": False,
                "upstream_dependencies": [
                    "v12:/execution/quality/latest",
                    f"v12:/portfolio/equity-history/live?limit={self.METRICS_EQUITY_HISTORY_LIMIT}",
                ],
            },
            "counts": {
                "equity_history_points": len(equity_points),
            },
            "raw": {
                "execution_quality": execution_quality,
                "equity_history": equity_history,
            },
        }

    def _normalize_positions(self, payload: dict, execution_quality: dict | None = None, *, include_debug_fields: bool = False) -> list[dict]:
        raw_positions = payload.get('items') or payload.get('positions') or []
        positions = []
        for row in raw_positions:
            weight = float(row.get('weight', row.get('target_weight', 0.0)) or 0.0)
            side = str(row.get('side', 'long') or 'long').lower()
            if side == 'short' and weight > 0:
                weight = -weight
            notional = float(row.get('notional', row.get('notional_usd', 0.0)) or 0.0)
            timestamp = row.get('timestamp') or row.get('updated_at') or row.get('created_at') or payload.get('as_of')
            item = {
                'symbol': row.get('symbol', 'unknown'),
                'side': side,
                'weight': round(weight, 6),
                'notional': round(notional, 2),
                'pnl': float(row.get('pnl', row.get('unrealized_pnl', 0.0)) or 0.0),
                'quantity': round(float(row.get('quantity', row.get('qty', 0.0)) or 0.0), 6),
                'avg_price': round(float(row.get('avg_price', row.get('avg_entry_price', 0.0)) or 0.0), 6),
                'mark_price': round(float(row.get('mark_price', row.get('markPrice', 0.0)) or 0.0), 6),
                'strategy_id': row.get('strategy_id') or row.get('run_id') or payload.get('run_id'),
                'alpha_family': row.get('alpha_family') or '',
                'timestamp': timestamp,
            }
            if include_debug_fields:
                item.update(
                    {
                        'price_source': row.get('price_source'),
                        'quote_time': row.get('quote_time'),
                        'quote_age_sec': float(row.get('quote_age_sec', 0.0) or 0.0),
                        'stale': bool(row.get('stale', False)),
                        'run_id': row.get('run_id') or payload.get('run_id'),
                        'timestamp': timestamp,
                    }
                )
            positions.append(item)
        if include_debug_fields:
            return positions

        equity_denom = self._safe_float(payload.get('total_equity') or payload.get('portfolio_value'))
        aggregated: dict[str, dict] = {}
        for item in positions:
            symbol = str(item.get('symbol') or 'unknown')
            side_sign = -1.0 if item.get('side') == 'short' else 1.0
            qty = self._safe_float(item.get('quantity'))
            notional = self._safe_float(item.get('notional'))
            pnl = self._safe_float(item.get('pnl'))
            mark_price = self._safe_float(item.get('mark_price'))
            avg_price = self._safe_float(item.get('avg_price'))
            strategy_id = str(item.get('strategy_id') or '')
            alpha_family = str(item.get('alpha_family') or '')
            signed_qty = side_sign * qty
            signed_notional = side_sign * notional
            signed_avg_value = signed_qty * avg_price

            bucket = aggregated.setdefault(
                symbol,
                {
                    'symbol': symbol,
                    'signed_qty': 0.0,
                    'signed_notional': 0.0,
                    'pnl': 0.0,
                    'signed_avg_value': 0.0,
                    'mark_price': mark_price,
                    'total_abs_qty': 0.0,
                    'primary_strategy_id': '',
                    'primary_alpha_family': '',
                    'primary_timestamp': None,
                    'primary_abs_notional': 0.0,
                },
            )
            bucket['signed_qty'] += signed_qty
            bucket['signed_notional'] += signed_notional
            bucket['pnl'] += pnl
            bucket['signed_avg_value'] += signed_avg_value
            bucket['mark_price'] = mark_price or bucket['mark_price']
            bucket['total_abs_qty'] += abs(qty)
            row_ts = self._parse_iso_timestamp(item.get('timestamp'))
            abs_notional = abs(notional)
            primary_ts = bucket.get('primary_timestamp')
            primary_abs_notional = self._safe_float(bucket.get('primary_abs_notional'))
            should_replace_primary = False
            if row_ts is not None:
                should_replace_primary = primary_ts is None or row_ts >= primary_ts
            elif primary_ts is None and abs_notional >= primary_abs_notional:
                should_replace_primary = True
            if should_replace_primary:
                bucket['primary_strategy_id'] = strategy_id
                bucket['primary_alpha_family'] = alpha_family
                bucket['primary_timestamp'] = row_ts
                bucket['primary_abs_notional'] = abs_notional

        reduced: list[dict] = []
        for symbol, bucket in aggregated.items():
            signed_qty = self._safe_float(bucket['signed_qty'])
            signed_notional = self._safe_float(bucket['signed_notional'])
            mark_price = self._safe_float(bucket['mark_price'])
            if abs(signed_qty) > 1e-12:
                avg_price = bucket['signed_avg_value'] / signed_qty
            else:
                avg_price = 0.0
            side = 'short' if signed_qty < 0 or signed_notional < 0 else 'long'
            notional = abs(signed_notional)
            if equity_denom > 1e-12:
                weight = signed_notional / equity_denom
            else:
                weight = sum(
                    self._safe_float(row.get('weight'))
                    for row in positions
                    if str(row.get('symbol') or 'unknown') == symbol
                )
            reduced.append(
                {
                    'symbol': symbol,
                    'side': side,
                    'weight': round(weight, 6),
                    'notional': round(notional, 2),
                    'pnl': round(self._safe_float(bucket['pnl']), 6),
                    'quantity': round(abs(signed_qty), 6),
                    'avg_price': round(avg_price, 6),
                    'mark_price': round(mark_price, 6),
                    'strategy_id': str(bucket.get('primary_strategy_id') or ''),
                    'alpha_family': str(bucket.get('primary_alpha_family') or ''),
                }
            )
        reduced.sort(key=lambda row: (-abs(self._safe_float(row.get('notional'))), str(row.get('symbol') or '')))
        return reduced
