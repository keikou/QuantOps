from __future__ import annotations

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

    async def get_orders(self, limit: int = DEFAULT_EXECUTION_ROW_LIMIT) -> dict:
        payload = await self.v12_client.get_execution_orders(limit=limit)
        items = payload.get('items', [])
        return {'status': payload.get('status', 'ok'), 'items': self._latest_orders(items, limit), 'as_of': payload.get('as_of') or utc_now_iso(), 'limit': limit}

    async def get_fills(self, limit: int = DEFAULT_EXECUTION_ROW_LIMIT) -> dict:
        payload = await self.v12_client.get_execution_fills(limit=limit)
        items = payload.get('items', [])
        return {'status': payload.get('status', 'ok'), 'items': self._latest_fills(items, limit), 'as_of': payload.get('as_of') or utc_now_iso(), 'limit': limit}

    async def get_state_latest(self) -> dict:
        payload = await self.v12_client.get_execution_state_latest()
        payload.setdefault('status', 'ok')
        payload.setdefault('as_of', utc_now_iso())
        return payload

    async def get_block_reasons_latest(self) -> dict:
        payload = await self.v12_client.get_execution_block_reasons_latest()
        return {'status': payload.get('status', 'ok'), 'items': payload.get('items', payload.get('block_reasons', [])), 'as_of': payload.get('as_of') or utc_now_iso()}
