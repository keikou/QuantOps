from __future__ import annotations

from datetime import datetime, timezone

from app.clients.v12_client import V12Client, utc_now_iso


DEFAULT_EXECUTION_ROW_LIMIT = 100


class ExecutionService:
    def __init__(self, v12_client: V12Client) -> None:
        self.v12_client = v12_client

    async def get_planner_latest(self) -> dict:
        payload = await self.v12_client.get_execution_planner_latest()
        payload.setdefault('status', 'ok')
        payload.setdefault('as_of', utc_now_iso())
        return payload

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
        }

    async def get_orders(self, limit: int = DEFAULT_EXECUTION_ROW_LIMIT) -> dict:
        payload = await self.v12_client.get_execution_orders(limit=limit)
        items = payload.get('items', [])
        return self._decorate_feed(payload, items=self._latest_orders(items, limit), limit=limit)

    async def get_fills(self, limit: int = DEFAULT_EXECUTION_ROW_LIMIT) -> dict:
        payload = await self.v12_client.get_execution_fills(limit=limit)
        items = payload.get('items', [])
        return self._decorate_feed(payload, items=self._latest_fills(items, limit), limit=limit)

    async def get_state_latest(self) -> dict:
        payload = await self.v12_client.get_execution_state_latest()
        payload.setdefault('status', 'ok')
        payload.setdefault('as_of', utc_now_iso())
        return payload

    async def get_block_reasons_latest(self) -> dict:
        payload = await self.v12_client.get_execution_block_reasons_latest()
        return {'status': payload.get('status', 'ok'), 'items': payload.get('items', payload.get('block_reasons', [])), 'as_of': payload.get('as_of') or utc_now_iso()}
