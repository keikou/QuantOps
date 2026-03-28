from __future__ import annotations

from ai_hedge_bot.core.enums import Mode
from ai_hedge_bot.services.runtime.runtime_service import RuntimeService


class LiveTradingService:
    def __init__(self) -> None:
        self.runtime_service = RuntimeService()

    def _route_live_intent(self, *, symbol: str, urgency: str, target_weight: float) -> dict:
        if urgency == "high" or target_weight >= 0.25:
            return {"venue": "binance_live", "order_type": "market", "tif": "IOC"}
        if target_weight >= 0.12:
            return {"venue": "binance_live", "order_type": "limit", "tif": "GTC"}
        return {"venue": "binance_live", "order_type": "limit", "tif": "GTC"}

    def evaluate_live_intent(
        self,
        *,
        symbol: str,
        urgency: str,
        target_weight: float,
        approved: bool,
        mode: Mode | str | None = None,
    ) -> dict:
        if isinstance(mode, Mode):
            effective_mode = mode.value.lower()
        else:
            effective_mode = str(mode or Mode.PAPER.value).lower()
        trading_state = str(self.runtime_service.get_trading_state().get("trading_state") or "running").lower()

        if not approved:
            return {
                "status": "blocked",
                "decision": "live_block",
                "reason_code": "live_not_approved",
                "trading_state": trading_state,
                "mode": effective_mode,
                "symbol": symbol,
            }

        if trading_state in {"halted", "paused"}:
            return {
                "status": "blocked",
                "decision": "live_block",
                "reason_code": "execution_disabled",
                "trading_state": trading_state,
                "mode": effective_mode,
                "symbol": symbol,
            }

        if effective_mode != Mode.LIVE.value:
            return {
                "status": "blocked",
                "decision": "live_block",
                "reason_code": "live_mode_disabled",
                "trading_state": trading_state,
                "mode": effective_mode,
                "symbol": symbol,
            }

        route = self._route_live_intent(symbol=symbol, urgency=urgency, target_weight=target_weight)
        return {
            "status": "ok",
            "decision": "live_send",
            "reason_code": None,
            "trading_state": trading_state,
            "mode": effective_mode,
            "symbol": symbol,
            "route": {
                "venue": route.get("venue"),
                "order_type": route.get("order_type"),
                "tif": route.get("tif"),
            },
        }
