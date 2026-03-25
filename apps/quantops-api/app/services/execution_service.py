from __future__ import annotations

import asyncio
from datetime import datetime, timezone

from app.clients.v12_client import V12Client, utc_now_iso


DEFAULT_EXECUTION_ROW_LIMIT = 100


class ExecutionService:
    FEED_CACHE_TTL_SECONDS = 5.0

    def __init__(self, v12_client: V12Client) -> None:
        self.v12_client = v12_client
        self._view_cache: dict | None = None
        self._view_inflight: asyncio.Task | None = None
        self._planner_cache: dict | None = None
        self._planner_inflight: asyncio.Task | None = None
        self._state_cache: dict | None = None
        self._state_inflight: asyncio.Task | None = None
        self._orders_cache: dict[int, dict] = {}
        self._orders_inflight: dict[int, asyncio.Task] = {}
        self._fills_cache: dict[int, dict] = {}
        self._fills_inflight: dict[int, asyncio.Task] = {}

    @staticmethod
    def _cache_age_sec(payload: dict | None) -> float | None:
        if not isinstance(payload, dict):
            return None
        return ExecutionService._snapshot_age_sec(payload.get("_cached_at"))

    async def get_planner_latest(self) -> dict:
        async def builder() -> dict:
            payload = await self.v12_client.get_execution_planner_latest()
            payload.setdefault('status', 'ok')
            payload.setdefault('as_of', utc_now_iso())
            payload.setdefault('build_status', 'live')
            payload.setdefault('source_snapshot_time', payload.get('as_of'))
            payload.setdefault('data_freshness_sec', self._snapshot_age_sec(payload.get('source_snapshot_time') or payload.get('as_of')))
            payload['_cached_at'] = utc_now_iso()
            return payload

        return await self._coalesced_summary(cache_name='_planner_cache', inflight_name='_planner_inflight', builder=builder)

    async def get_view_latest(self) -> dict:
        async def builder() -> dict:
            payload = await self.v12_client.get_execution_view_latest()
            if isinstance(payload, dict) and isinstance(payload.get('planner'), dict) and isinstance(payload.get('state'), dict):
                planner = dict(payload.get('planner') or {})
                state = dict(payload.get('state') or {})
            else:
                planner, state = await asyncio.gather(
                    self.v12_client.get_execution_planner_latest(),
                    self.v12_client.get_execution_state_latest(),
                )
                planner = planner if isinstance(planner, dict) else {}
                state = state if isinstance(state, dict) else {}
            planner.setdefault('status', 'ok')
            planner.setdefault('as_of', utc_now_iso())
            planner.setdefault('build_status', 'live')
            planner.setdefault('source_snapshot_time', planner.get('as_of'))
            planner.setdefault('data_freshness_sec', self._snapshot_age_sec(planner.get('source_snapshot_time') or planner.get('as_of')))
            state.setdefault('status', 'ok')
            state.setdefault('as_of', utc_now_iso())
            state.setdefault('build_status', 'live')
            state.setdefault('source_snapshot_time', state.get('as_of'))
            state.setdefault('data_freshness_sec', self._snapshot_age_sec(state.get('source_snapshot_time') or state.get('as_of')))
            as_of = state.get('as_of') or planner.get('as_of') or utc_now_iso()
            source_snapshot_time = state.get('source_snapshot_time') or planner.get('source_snapshot_time') or as_of
            build_status = 'fresh_cache' if planner.get('build_status') == 'fresh_cache' and state.get('build_status') == 'fresh_cache' else 'live'
            return {
                'status': 'ok',
                'planner': planner,
                'state': state,
                'as_of': as_of,
                'source_snapshot_time': source_snapshot_time,
                'data_freshness_sec': self._snapshot_age_sec(source_snapshot_time),
                'build_status': build_status,
                '_cached_at': utc_now_iso(),
            }

        return await self._coalesced_summary(cache_name='_view_cache', inflight_name='_view_inflight', builder=builder)

    def _sort_key(self, row: dict) -> tuple[str, str, str]:
        return (
            str(row.get('updated_at') or row.get('updatedAt') or ''),
            str(row.get('created_at') or row.get('createdAt') or row.get('submit_time') or row.get('submitTime') or ''),
            str(row.get('as_of') or row.get('asOf') or ''),
        )

    def _latest_orders(self, rows: list[dict], limit: int) -> list[dict]:
        latest_by_order: dict[str, dict] = {}
        for row in rows:
            order_id = str(row.get('order_id') or row.get('orderId') or '')
            if not order_id:
                continue
            existing = latest_by_order.get(order_id)
            if existing is None or self._sort_key(row) >= self._sort_key(existing):
                latest_by_order[order_id] = row
        ordered = sorted(latest_by_order.values(), key=self._sort_key, reverse=True)
        return ordered[: max(1, limit)]

    def _latest_fills(self, rows: list[dict], limit: int) -> list[dict]:
        ordered = sorted(rows, key=self._sort_key, reverse=True)
        return ordered[: max(1, limit)]

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

    def _decorate_feed(self, payload: dict, *, items: list[dict], limit: int) -> dict:
        as_of = payload.get('as_of') or utc_now_iso()
        return {
            'status': payload.get('status', 'ok'),
            'items': items,
            'as_of': as_of,
            'limit': limit,
            'build_status': 'live',
            'source_snapshot_time': as_of,
            'data_freshness_sec': self._snapshot_age_sec(as_of),
            '_cached_at': utc_now_iso(),
        }

    def _is_fresh_payload(self, payload: dict | None) -> bool:
        if not isinstance(payload, dict):
            return False
        age = self._snapshot_age_sec(payload.get('source_snapshot_time') or payload.get('as_of'))
        return age is not None and age <= self.FEED_CACHE_TTL_SECONDS

    async def _coalesced_feed(self, *, cache: dict[int, dict], inflight: dict[int, asyncio.Task], limit: int, builder) -> dict:
        cached = cache.get(limit)
        cache_age = self._cache_age_sec(cached)
        if cache_age is not None and cache_age <= self.FEED_CACHE_TTL_SECONDS:
            result = dict(cached)
            result['build_status'] = 'fresh_cache'
            result['data_freshness_sec'] = self._snapshot_age_sec(result.get('source_snapshot_time') or result.get('as_of'))
            result.pop('_cached_at', None)
            return result

        existing = inflight.get(limit)
        if existing is not None and not existing.done():
            payload = await existing
            result = dict(payload)
            result['build_status'] = 'fresh_cache'
            result['data_freshness_sec'] = self._snapshot_age_sec(result.get('source_snapshot_time') or result.get('as_of'))
            result.pop('_cached_at', None)
            return result

        task = asyncio.create_task(builder())
        inflight[limit] = task
        try:
            payload = await task
            cache[limit] = payload
            result = dict(payload)
            result.pop('_cached_at', None)
            return result
        finally:
            if inflight.get(limit) is task:
                inflight.pop(limit, None)

    async def get_orders(self, limit: int = DEFAULT_EXECUTION_ROW_LIMIT) -> dict:
        async def builder() -> dict:
            payload = await self.v12_client.get_execution_orders(limit=limit)
            items = payload.get('items', [])
            return self._decorate_feed(payload, items=self._latest_orders(items, limit), limit=limit)

        return await self._coalesced_feed(cache=self._orders_cache, inflight=self._orders_inflight, limit=limit, builder=builder)

    async def get_fills(self, limit: int = DEFAULT_EXECUTION_ROW_LIMIT) -> dict:
        async def builder() -> dict:
            payload = await self.v12_client.get_execution_fills(limit=limit)
            items = payload.get('items', [])
            return self._decorate_feed(payload, items=self._latest_fills(items, limit), limit=limit)

        return await self._coalesced_feed(cache=self._fills_cache, inflight=self._fills_inflight, limit=limit, builder=builder)

    async def get_state_latest(self) -> dict:
        async def builder() -> dict:
            payload = await self.v12_client.get_execution_state_latest()
            payload.setdefault('status', 'ok')
            payload.setdefault('as_of', utc_now_iso())
            payload.setdefault('build_status', 'live')
            payload.setdefault('source_snapshot_time', payload.get('as_of'))
            payload.setdefault('data_freshness_sec', self._snapshot_age_sec(payload.get('source_snapshot_time') or payload.get('as_of')))
            payload['_cached_at'] = utc_now_iso()
            return payload

        return await self._coalesced_summary(cache_name='_state_cache', inflight_name='_state_inflight', builder=builder)

    async def get_block_reasons_latest(self) -> dict:
        payload = await self.v12_client.get_execution_block_reasons_latest()
        return {'status': payload.get('status', 'ok'), 'items': payload.get('items', payload.get('block_reasons', [])), 'as_of': payload.get('as_of') or utc_now_iso()}

    async def _coalesced_summary(self, *, cache_name: str, inflight_name: str, builder) -> dict:
        cached = getattr(self, cache_name)
        cache_age = self._cache_age_sec(cached)
        if cache_age is not None and cache_age <= self.FEED_CACHE_TTL_SECONDS:
            result = dict(cached)
            result['build_status'] = 'fresh_cache'
            result['data_freshness_sec'] = self._snapshot_age_sec(result.get('source_snapshot_time') or result.get('as_of'))
            result.pop('_cached_at', None)
            return result

        existing = getattr(self, inflight_name)
        if existing is not None and not existing.done():
            payload = await existing
            result = dict(payload)
            result['build_status'] = 'fresh_cache'
            result['data_freshness_sec'] = self._snapshot_age_sec(result.get('source_snapshot_time') or result.get('as_of'))
            result.pop('_cached_at', None)
            return result

        task = asyncio.create_task(builder())
        setattr(self, inflight_name, task)
        try:
            payload = await task
            setattr(self, cache_name, payload)
            result = dict(payload)
            result.pop('_cached_at', None)
            return result
        finally:
            if getattr(self, inflight_name) is task:
                setattr(self, inflight_name, None)
