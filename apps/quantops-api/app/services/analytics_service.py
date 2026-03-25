from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
import logging

from app.clients.v12_client import V12Client, utc_now_iso
from app.repositories.analytics_repository import AnalyticsRepository


logger = logging.getLogger(__name__)


class AnalyticsService:
    EQUITY_HISTORY_CACHE_TTL_SECONDS = 5.0
    EQUITY_HISTORY_STALE_MAX_AGE_SECONDS = 60.0

    def __init__(self, v12_client: V12Client, analytics_repository: AnalyticsRepository) -> None:
        self.v12_client = v12_client
        self.analytics_repository = analytics_repository
        self._equity_history_cache: dict | None = None
        self._equity_history_cache_expires_at: datetime | None = None
        self._equity_history_cache_updated_at: datetime | None = None
        self._equity_history_inflight_task: asyncio.Task | None = None

    def _get_cached_equity_history(self, *, allow_stale: bool = False) -> dict | None:
        expires_at = self._equity_history_cache_expires_at
        updated_at = self._equity_history_cache_updated_at
        if self._equity_history_cache is None or expires_at is None or updated_at is None:
            return None
        now = datetime.now(timezone.utc)
        if expires_at > now:
            return dict(self._equity_history_cache)
        if not allow_stale:
            return None
        if (now - updated_at).total_seconds() > self.EQUITY_HISTORY_STALE_MAX_AGE_SECONDS:
            return None
        return dict(self._equity_history_cache)

    async def _build_equity_history_live(self) -> dict:
        payload = await self.v12_client.get_equity_history()
        items = payload.get('items') or []
        if items:
            result = {'items': items, 'as_of': payload.get('as_of') or items[-1].get('as_of')}
        else:
            series = self.analytics_repository.pnl_series(limit=200)
            if not series:
                result = {'items': [], 'base_equity': 100000.0, 'as_of': utc_now_iso()}
            else:
                base_equity = 100000.0
                cumulative = 0.0
                built_items = []
                for row in series:
                    cumulative += float(row.get('total_pnl', 0.0) or 0.0)
                    label = str(row.get('as_of', utc_now_iso()))
                    built_items.append({'name': label, 'value': round(base_equity + cumulative, 6), 'pnl': round(cumulative, 6), 'as_of': label})
                result = {'items': built_items, 'base_equity': base_equity, 'as_of': built_items[-1]['as_of'] if built_items else utc_now_iso()}
        now = datetime.now(timezone.utc)
        self._equity_history_cache = dict(result)
        self._equity_history_cache_updated_at = now
        self._equity_history_cache_expires_at = now + timedelta(seconds=self.EQUITY_HISTORY_CACHE_TTL_SECONDS)
        return result

    def _schedule_equity_history_refresh(self) -> None:
        task = self._equity_history_inflight_task
        if task is not None and not task.done():
            return
        self._equity_history_inflight_task = asyncio.create_task(self._build_equity_history_live())

        def _clear_task(finished: asyncio.Task) -> None:
            try:
                finished.exception()
            except Exception:
                logger.exception("analytics_equity_history_background_refresh_failed")
            finally:
                if self._equity_history_inflight_task is finished:
                    self._equity_history_inflight_task = None

        self._equity_history_inflight_task.add_done_callback(_clear_task)

    async def refresh(self) -> dict:
        registry = await self.v12_client.get_strategy_registry()
        global_dash = await self.v12_client.get_global_dashboard()
        exec_quality = await self.v12_client.get_execution_quality()
        risk_budget = await self.v12_client.get_risk_budget()

        strategies = registry.get("strategies", [])
        aggregate = (global_dash.get("strategy") or {}).get("aggregate", {})
        per_strategy_risk = {row.get("strategy_id"): row for row in (risk_budget.get("risk") or {}).get("per_strategy", [])}

        alpha_rows: list[dict] = []
        base_hit = float(aggregate.get("avg_hit_rate", 0.55) or 0.55)
        for idx, row in enumerate(strategies):
            capital_weight = float(row.get("capital_weight", 0.0) or 0.0)
            risk_row = per_strategy_risk.get(row.get("strategy_id"), {})
            budget_usage = float(risk_row.get("budget_usage", 0.72 + idx * 0.03) or 0.72 + idx * 0.03)
            pnl = round(capital_weight * (0.012 - idx * 0.0013), 6)
            sharpe = round(1.6 - idx * 0.18 + capital_weight, 4)
            drawdown = round(max(0.01, budget_usage * 0.055), 6)
            hit_rate = round(max(0.35, min(0.9, base_hit - idx * 0.03)), 6)
            turnover = round(0.18 + idx * 0.05, 6)
            rank_score = round((sharpe * 0.35) + ((1 - drawdown) * 0.35) + (hit_rate * 0.2) + (capital_weight * 0.1), 6)
            alpha_rows.append({
                "strategy_id": row.get("strategy_id", f"s{idx+1}"),
                "strategy_name": row.get("strategy_name", row.get("strategy_id", f"strategy_{idx+1}")),
                "pnl": pnl,
                "sharpe": sharpe,
                "drawdown": drawdown,
                "hit_rate": hit_rate,
                "turnover": turnover,
                "rank_score": rank_score,
            })

        if not alpha_rows:
            alpha_rows = [{"strategy_id": "paper-default", "strategy_name": "paper-default", "pnl": 0.0, "sharpe": 0.0, "drawdown": 0.0, "hit_rate": 0.0, "turnover": 0.0, "rank_score": 0.0}]

        self.analytics_repository.insert_alpha_snapshot(alpha_rows)
        fill_rate = max(0.0, min(1.0, float(exec_quality.get("fill_rate", 0.0) or 0.0)))
        slippage = float(exec_quality.get("avg_slippage_bps", 0.0) or 0.0)
        p95 = float(exec_quality.get("latency_ms_p95", 0.0) or 0.0)
        venue_score = round(max(0.0, min(1.0, fill_rate - (slippage / 1000.0) - (p95 / 5000.0))), 6)
        execution_row = {
            "fill_rate": fill_rate,
            "avg_slippage_bps": slippage,
            "latency_ms_p50": float(exec_quality.get("latency_ms_p50", 0.0) or 0.0),
            "latency_ms_p95": p95,
            "venue_score": venue_score,
        }
        self.analytics_repository.insert_execution_snapshot(execution_row)

        return {"ok": True, "alpha_count": len(alpha_rows), "execution": execution_row, "as_of": utc_now_iso()}

    def alpha_ranking(self) -> dict:
        rows = self.analytics_repository.latest_alpha_rows()
        return {
            "items": rows,
            "top_alpha": rows[0] if rows else None,
            "count": len(rows),
            "as_of": rows[0]["as_of"] if rows else utc_now_iso(),
        }

    def pnl_summary(self) -> dict:
        ranking = self.analytics_repository.latest_alpha_rows()
        series = self.analytics_repository.pnl_series()
        total = round(sum(float(row.get("pnl", 0.0) or 0.0) for row in ranking), 6)
        return {
            "total_pnl": total,
            "best_strategy": max(ranking, key=lambda x: x.get("pnl", 0.0), default=None),
            "series": series,
            "as_of": ranking[0]["as_of"] if ranking else utc_now_iso(),
        }

    def sharpe_summary(self) -> dict:
        ranking = self.analytics_repository.latest_alpha_rows()
        avg = round(sum(float(row.get("sharpe", 0.0) or 0.0) for row in ranking) / max(len(ranking), 1), 6)
        return {
            "average_sharpe": avg,
            "items": [{"strategy_id": row["strategy_id"], "strategy_name": row["strategy_name"], "sharpe": row["sharpe"]} for row in ranking],
            "as_of": ranking[0]["as_of"] if ranking else utc_now_iso(),
        }

    def drawdown_summary(self) -> dict:
        ranking = self.analytics_repository.latest_alpha_rows()
        series = self.analytics_repository.drawdown_series()
        worst = max(ranking, key=lambda x: x.get("drawdown", 0.0), default=None)
        return {
            "max_drawdown": float(worst.get("drawdown", 0.0) if worst else 0.0),
            "worst_strategy": worst,
            "series": series,
            "as_of": ranking[0]["as_of"] if ranking else utc_now_iso(),
        }

    def execution_summary(self) -> dict:
        latest = self.analytics_repository.latest_execution()
        if latest is None:
            latest = {"fill_rate": 0.0, "avg_slippage_bps": 0.0, "latency_ms_p50": 0.0, "latency_ms_p95": 0.0, "venue_score": 0.0, "as_of": utc_now_iso()}
        latest['fill_rate'] = max(0.0, min(1.0, float(latest.get('fill_rate', 0.0) or 0.0)))
        latest['venue_score'] = max(0.0, min(1.0, float(latest.get('venue_score', 0.0) or 0.0)))
        return latest

    async def execution_summary_live(self) -> dict:
        latest = self.execution_summary()
        looks_empty = (
            float(latest.get('fill_rate', 0.0) or 0.0) == 0.0
            and float(latest.get('avg_slippage_bps', 0.0) or 0.0) == 0.0
            and float(latest.get('latency_ms_p50', 0.0) or 0.0) == 0.0
            and float(latest.get('latency_ms_p95', 0.0) or 0.0) == 0.0
            and float(latest.get('venue_score', 0.0) or 0.0) == 0.0
        )
        if not looks_empty:
            latest.setdefault('status', 'ok')
            return latest

        upstream = await self.v12_client.get_execution_quality()
        fill_rate = max(0.0, min(1.0, float(upstream.get('fill_rate', 0.0) or 0.0)))
        slippage = float(upstream.get('avg_slippage_bps', 0.0) or 0.0)
        p50 = float(upstream.get('latency_ms_p50', 0.0) or 0.0)
        p95 = float(upstream.get('latency_ms_p95', 0.0) or 0.0)
        venue_score = float(upstream.get('venue_score', 0.0) or 0.0)
        if venue_score == 0.0 and (fill_rate > 0.0 or slippage > 0.0 or p95 > 0.0):
            venue_score = round(max(0.0, min(1.0, fill_rate - (slippage / 1000.0) - (p95 / 5000.0))), 6)
        live = {
            'fill_rate': fill_rate,
            'avg_slippage_bps': slippage,
            'latency_ms_p50': p50,
            'latency_ms_p95': p95,
            'venue_score': max(0.0, min(1.0, venue_score)),
            'as_of': upstream.get('as_of') or utc_now_iso(),
            'status': upstream.get('status', 'ok'),
        }
        if fill_rate > 0.0 or slippage > 0.0 or p50 > 0.0 or p95 > 0.0 or live['venue_score'] > 0.0:
            self.analytics_repository.insert_execution_snapshot(live)
        return live

    def runtime_states(self) -> list[dict]:
        return self.analytics_repository.runtime_states()

    async def equity_history(self) -> dict:
        cached = self._get_cached_equity_history()
        if cached is not None:
            return cached

        stale_cached = self._get_cached_equity_history(allow_stale=True)
        if stale_cached is not None:
            self._schedule_equity_history_refresh()
            return stale_cached

        task = self._equity_history_inflight_task
        if task is not None and not task.done():
            return await task

        task = asyncio.create_task(self._build_equity_history_live())
        self._equity_history_inflight_task = task
        try:
            return await task
        finally:
            if self._equity_history_inflight_task is task:
                self._equity_history_inflight_task = None

    async def latest_execution_fills(self) -> dict:
        payload = await self.v12_client.get_execution_fills(limit=100)
        fills = payload.get('items') or payload.get('latest_fills') or payload.get('fills') or []
        return {'items': fills[:100], 'as_of': payload.get('as_of') or utc_now_iso(), 'limit': 100}

    async def latest_execution_planner(self) -> dict:
        payload = await self.v12_client.get_execution_planner_latest()
        return {
            'trading_state': payload.get('trading_state') or 'unknown',
            'plan_count': int(payload.get('plan_count', 0) or 0),
            'expired_count': int(payload.get('expired_count', 0) or 0),
            'algo_mix': payload.get('algo_mix') or {},
            'route_mix': payload.get('route_mix') or {},
            'items': payload.get('items') or [],
            'as_of': payload.get('as_of') or utc_now_iso(),
        }
