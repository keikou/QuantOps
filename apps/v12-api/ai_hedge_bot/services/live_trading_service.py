from __future__ import annotations

from ai_hedge_bot.app.container import CONTAINER
from ai_hedge_bot.core.ids import new_cycle_id
from ai_hedge_bot.core.clock import utc_now_iso
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

    def submit_live_order(
        self,
        *,
        symbol: str,
        side: str,
        qty: float,
        urgency: str,
        target_weight: float,
        approved: bool,
        mode: Mode | str | None = None,
    ) -> dict:
        decision = self.evaluate_live_intent(
            symbol=symbol,
            urgency=urgency,
            target_weight=target_weight,
            approved=approved,
            mode=mode,
        )
        if decision["status"] != "ok":
            return decision

        now = utc_now_iso()
        live_order_id = new_cycle_id()
        venue_order_id = f"venue-{live_order_id}"
        route = decision["route"]
        CONTAINER.runtime_store.append(
            "live_orders",
            {
                "live_order_id": live_order_id,
                "created_at": now,
                "updated_at": now,
                "symbol": symbol,
                "side": side,
                "qty": qty,
                "venue": route["venue"],
                "order_type": route["order_type"],
                "tif": route["tif"],
                "decision_id": live_order_id,
                "status": "submitted",
                "venue_order_id": venue_order_id,
                "metadata_json": CONTAINER.runtime_store.to_json(
                    {
                        "urgency": urgency,
                        "target_weight": target_weight,
                        "decision": decision["decision"],
                    }
                ),
            },
        )
        CONTAINER.runtime_store.append(
            "live_reconciliation_events",
            {
                "reconciliation_event_id": new_cycle_id(),
                "created_at": now,
                "live_order_id": live_order_id,
                "venue_order_id": venue_order_id,
                "event_type": "order_submitted",
                "status": "pending",
                "matched": True,
                "details_json": CONTAINER.runtime_store.to_json({"symbol": symbol, "venue": route["venue"]}),
            },
        )
        return {
            **decision,
            "live_order_id": live_order_id,
            "venue_order_id": venue_order_id,
            "order_status": "submitted",
        }

    def reconcile_live_fill(
        self,
        *,
        live_order_id: str,
        venue_order_id: str,
        symbol: str,
        side: str,
        fill_qty: float,
        fill_price: float,
        asset: str = "USDT",
        free_balance: float = 0.0,
        locked_balance: float = 0.0,
        matched: bool = True,
    ) -> dict:
        now = utc_now_iso()
        fill_status = "filled" if matched else "mismatch"
        CONTAINER.runtime_store.execute(
            """
            UPDATE live_orders
            SET status = ?, updated_at = ?
            WHERE live_order_id = ?
            """,
            [fill_status, now, live_order_id],
        )
        CONTAINER.runtime_store.append(
            "live_fills",
            {
                "live_fill_id": new_cycle_id(),
                "created_at": now,
                "live_order_id": live_order_id,
                "venue_order_id": venue_order_id,
                "symbol": symbol,
                "side": side,
                "fill_qty": fill_qty,
                "fill_price": fill_price,
                "status": fill_status,
                "metadata_json": CONTAINER.runtime_store.to_json({"matched": matched}),
            },
        )
        CONTAINER.runtime_store.append(
            "live_account_balances",
            {
                "balance_snapshot_id": new_cycle_id(),
                "created_at": now,
                "venue": "binance_live",
                "asset": asset,
                "free_balance": free_balance,
                "locked_balance": locked_balance,
                "total_balance": free_balance + locked_balance,
                "source": "reconciliation",
            },
        )
        CONTAINER.runtime_store.append(
            "live_reconciliation_events",
            {
                "reconciliation_event_id": new_cycle_id(),
                "created_at": now,
                "live_order_id": live_order_id,
                "venue_order_id": venue_order_id,
                "event_type": "fill_reconciled" if matched else "fill_mismatch",
                "status": "ok" if matched else "incident",
                "matched": matched,
                "details_json": CONTAINER.runtime_store.to_json(
                    {
                        "symbol": symbol,
                        "fill_qty": fill_qty,
                        "fill_price": fill_price,
                        "free_balance": free_balance,
                        "locked_balance": locked_balance,
                    }
                ),
            },
        )
        if not matched:
            halt = self.runtime_service.halt_trading(
                "Live reconciliation mismatch detected",
                actor="live_reconciliation_guard",
            )
            CONTAINER.runtime_store.append(
                "live_incidents",
                {
                    "incident_id": new_cycle_id(),
                    "created_at": now,
                    "category": "reconciliation",
                    "severity": "high",
                    "status": "open",
                    "summary": "Live reconciliation mismatch detected",
                    "details_json": CONTAINER.runtime_store.to_json(
                        {
                            "live_order_id": live_order_id,
                            "venue_order_id": venue_order_id,
                            "guard_state": halt.get("trading_state"),
                        }
                    ),
                },
            )
        return {
            "status": "ok" if matched else "incident",
            "live_order_id": live_order_id,
            "venue_order_id": venue_order_id,
            "order_status": fill_status,
            "matched": matched,
        }
