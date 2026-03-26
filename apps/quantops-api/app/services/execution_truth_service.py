from __future__ import annotations

from typing import Any

from app.clients.v12_client import V12Client


class ExecutionTruthService:
    def __init__(self, v12_client: V12Client) -> None:
        self.v12_client = v12_client

    async def get_recent_fills(self, limit: int = 100) -> dict[str, Any]:
        payload = await self._call_v12("get_execution_fills", limit=limit)
        items = payload.get("items", []) if isinstance(payload, dict) else []
        rows = []
        for row in items:
            rows.append(
                {
                    "fill_id": row.get("fill_id"),
                    "order_id": row.get("order_id"),
                    "symbol": row.get("symbol"),
                    "side": row.get("side"),
                    "qty": row.get("qty") or row.get("fill_qty"),
                    "fill_price": row.get("fill_price"),
                    "price_source": row.get("price_source"),
                    "bid": row.get("bid"),
                    "ask": row.get("ask"),
                    "strategy_id": row.get("strategy_id"),
                    "alpha_family": row.get("alpha_family"),
                    "event_time": row.get("event_time") or row.get("created_at"),
                }
            )
        return {"status": "ok", "items": rows, "limit": limit}

    async def get_orders_latest(self, limit: int = 100) -> dict[str, Any]:
        payload = await self._call_v12("get_execution_orders", limit=limit)
        items = payload.get("items", []) if isinstance(payload, dict) else []
        return {"status": "ok", "items": items, "limit": limit}

    async def get_runtime_state(self) -> dict[str, Any]:
        payload = await self._call_v12("get_execution_state_latest")
        return payload if isinstance(payload, dict) else {"status": "unknown"}

    async def _call_v12(self, method_name: str, **kwargs) -> dict[str, Any]:
        method = getattr(self.v12_client, method_name, None)
        if callable(method):
            return await method(**kwargs)
        return {"status": "ok", "items": []}