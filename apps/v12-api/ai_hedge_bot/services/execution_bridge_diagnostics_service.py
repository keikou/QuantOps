from __future__ import annotations

import json
from typing import Any

from ai_hedge_bot.app.container import CONTAINER
from ai_hedge_bot.contracts.reason_codes import NO_POSITION_DELTA
from ai_hedge_bot.contracts.runtime_events import (
    CYCLE_COMPLETED,
    CYCLE_FAILED,
    CYCLE_STARTED,
    FILL_RECORDED,
    ORDER_BLOCKED,
    ORDER_SUBMITTED,
    PLANNER_GENERATED,
)
from ai_hedge_bot.repositories.runtime_repository import RuntimeRepository


class ExecutionBridgeDiagnosticsService:
    def __init__(self) -> None:
        self.runtime_repo = RuntimeRepository()
        self.store = CONTAINER.runtime_store

    def _latest_run_id(self) -> str | None:
        row = self.store.fetchone_dict(
            """
            SELECT run_id
            FROM runtime_events
            WHERE coalesce(run_id, '') <> ''
            ORDER BY timestamp DESC, created_at DESC
            LIMIT 1
            """
        )
        return str((row or {}).get("run_id") or "") or None

    def _load_events(self, run_id: str | None = None) -> list[dict[str, Any]]:
        resolved_run_id = run_id or self._latest_run_id()
        if not resolved_run_id:
            return []
        return self.runtime_repo.list_events(run_id=resolved_run_id, limit=500)

    @staticmethod
    def _signed_qty(row: dict[str, Any]) -> float:
        qty = float(row.get("order_qty", 0.0) or 0.0)
        side = str(row.get("side", "") or "").lower()
        return qty if side == "buy" else (-qty if side == "sell" else qty)

    def _derive_bridge_state(self, *, cycle_failed: bool, filled_count: int, submitted_count: int, planned_count: int, blocked_count: int, zero_submit_reason_code: str | None) -> str:
        if cycle_failed:
            return "failed"
        if filled_count > 0:
            return "filled"
        if submitted_count > 0 and filled_count == 0:
            return "submitted_no_fill"
        if planned_count > 0 and submitted_count == 0 and blocked_count > 0:
            return "planned_blocked"
        if planned_count > 0 and submitted_count == 0:
            return "planned_not_submitted"
        if planned_count == 0 and zero_submit_reason_code == NO_POSITION_DELTA:
            return "no_decision"
        if blocked_count > 0:
            return "planned_blocked"
        return "failed" if cycle_failed else "no_decision"

    def get_bridge_summary(self, run_id: str | None = None) -> dict[str, Any]:
        events = self._load_events(run_id=run_id)
        if not events:
            return {
                "status": "no_data",
                "run_id": None,
                "cycle_id": None,
                "cycle_status": "no_data",
                "planned_count": 0,
                "submitted_count": 0,
                "blocked_count": 0,
                "filled_count": 0,
                "zero_submit_reason_code": None,
                "zero_submit_reason_summary": None,
                "bridge_state": "no_decision",
                "latest_reason_code": None,
                "latest_reason_summary": None,
                "blocking_component": None,
                "degraded_flags": [],
                "event_chain_complete": False,
                "last_transition_at": None,
                "operator_message": "No runtime event chain is available yet.",
            }

        latest = events[0]
        run_id_value = latest.get("run_id")
        cycle_id = latest.get("cycle_id")
        planner_event = next((item for item in events if item.get("event_type") == PLANNER_GENERATED), None)
        cycle_failed = any(item.get("event_type") == CYCLE_FAILED for item in events)
        cycle_completed = any(item.get("event_type") == CYCLE_COMPLETED for item in events)
        started = any(item.get("event_type") == CYCLE_STARTED for item in events)
        planned_count = int((planner_event or {}).get("details", {}).get("plan_count", 0) or 0)
        submitted_count = sum(1 for item in events if item.get("event_type") == ORDER_SUBMITTED)
        blocked_events = [item for item in events if item.get("event_type") == ORDER_BLOCKED]
        blocked_count = len(blocked_events)
        filled_count = sum(1 for item in events if item.get("event_type") == FILL_RECORDED)
        reason_event = next((item for item in events if item.get("event_type") == ORDER_BLOCKED and item.get("reason_code")), None)
        if reason_event is None:
            reason_event = next((item for item in events if item.get("reason_code")), None)
        zero_submit_reason_code = None
        zero_submit_reason_summary = None
        if submitted_count == 0:
            zero_submit_reason_code = str((planner_event or {}).get("reason_code") or (reason_event or {}).get("reason_code") or "") or None
            zero_submit_reason_summary = str((planner_event or {}).get("summary") or (reason_event or {}).get("summary") or "") or None
        blocking_component = str((reason_event or {}).get("details", {}).get("blocking_component") or "") or None
        bridge_state = self._derive_bridge_state(
            cycle_failed=cycle_failed,
            filled_count=filled_count,
            submitted_count=submitted_count,
            planned_count=planned_count,
            blocked_count=blocked_count,
            zero_submit_reason_code=zero_submit_reason_code,
        )
        degraded_flags: list[str] = []
        for item in blocked_events:
            code = str(item.get("reason_code") or "")
            if code and code not in degraded_flags:
                degraded_flags.append(code)
        cycle_status = "failed" if cycle_failed else ("completed" if cycle_completed else "running")
        event_chain_complete = started and (cycle_completed or cycle_failed) and planner_event is not None
        operator_message = {
            "no_decision": "Planner generated no actionable decisions for this cycle.",
            "planned_blocked": "Plan generation completed, but the execution bridge blocked submission.",
            "planned_not_submitted": "Plan generation completed, but no child orders were submitted.",
            "submitted_no_fill": "Child orders were submitted, but no fills were recorded.",
            "filled": "Planner, execution bridge, and fills are connected for this cycle.",
            "failed": "The cycle failed before the planner-to-fill chain completed.",
        }.get(bridge_state, "Execution bridge state is unavailable.")
        return {
            "status": "ok",
            "run_id": run_id_value,
            "cycle_id": cycle_id,
            "cycle_status": cycle_status,
            "planned_count": planned_count,
            "submitted_count": submitted_count,
            "blocked_count": blocked_count,
            "filled_count": filled_count,
            "zero_submit_reason_code": zero_submit_reason_code,
            "zero_submit_reason_summary": zero_submit_reason_summary,
            "bridge_state": bridge_state,
            "latest_reason_code": str((reason_event or {}).get("reason_code") or "") or None,
            "latest_reason_summary": str((reason_event or {}).get("summary") or "") or None,
            "blocking_component": blocking_component,
            "degraded_flags": degraded_flags,
            "event_chain_complete": event_chain_complete,
            "last_transition_at": latest.get("timestamp") or latest.get("created_at"),
            "operator_message": operator_message,
        }

    def get_planner_truth(self, run_id: str | None = None) -> dict[str, Any]:
        summary = self.get_bridge_summary(run_id=run_id)
        resolved_run_id = summary.get("run_id")
        if not resolved_run_id:
            return {
                "status": "no_data",
                "run_id": None,
                "cycle_id": None,
                "generated_at": None,
                "planner_status": "no_data",
                "reason_code": None,
                "reason_summary": None,
                "items": [],
            }
        plans = self.store.fetchall_dict(
            """
            SELECT plan_id, created_at, run_id, mode, symbol, side, target_weight, order_qty, limit_price,
                   participation_rate, status, algo, route, expire_seconds, slice_count, metadata_json
            FROM execution_plans
            WHERE run_id = ?
            ORDER BY created_at DESC, symbol ASC
            """,
            [resolved_run_id],
        )
        order_counts = self.store.fetchall_dict(
            """
            SELECT plan_id,
                   COUNT(*) AS order_count,
                   SUM(CASE WHEN lower(coalesce(status, '')) IN ('submitted', 'partially_filled', 'filled', 'open') THEN 1 ELSE 0 END) AS active_count
            FROM execution_orders
            WHERE plan_id IN (SELECT plan_id FROM execution_plans WHERE run_id = ?)
            GROUP BY plan_id
            """,
            [resolved_run_id],
        )
        fill_counts = self.store.fetchall_dict(
            """
            SELECT plan_id, COUNT(*) AS fill_count
            FROM execution_fills
            WHERE run_id = ?
            GROUP BY plan_id
            """,
            [resolved_run_id],
        )
        blocked_events = self.runtime_repo.list_events(run_id=resolved_run_id, event_type=ORDER_BLOCKED, limit=200)
        orders_by_plan = {str(row.get("plan_id") or ""): row for row in order_counts}
        fills_by_plan = {str(row.get("plan_id") or ""): row for row in fill_counts}
        blocked_by_symbol: dict[str, dict[str, Any]] = {}
        for item in blocked_events:
            symbol = str(item.get("symbol") or "")
            if symbol and symbol not in blocked_by_symbol:
                blocked_by_symbol[symbol] = item
        items: list[dict[str, Any]] = []
        for plan in plans:
            metadata_json = plan.get("metadata_json")
            metadata = {}
            if isinstance(metadata_json, str) and metadata_json:
                try:
                    metadata = json.loads(metadata_json)
                except Exception:
                    metadata = {}
            plan_id = str(plan.get("plan_id") or "")
            symbol = str(plan.get("symbol") or "")
            order_info = orders_by_plan.get(plan_id, {})
            fill_info = fills_by_plan.get(plan_id, {})
            blocked = blocked_by_symbol.get(symbol, {})
            order_count = int(order_info.get("order_count", 0) or 0)
            fill_count = int(fill_info.get("fill_count", 0) or 0)
            has_child_orders = order_count > 0
            execution_status = "filled" if fill_count > 0 else ("submitted" if has_child_orders else "blocked")
            items.append({
                "plan_id": plan_id,
                "symbol": symbol,
                "side": plan.get("side"),
                "planned_qty": float(plan.get("order_qty", 0.0) or 0.0),
                "position_delta": self._signed_qty(plan),
                "has_child_orders": has_child_orders,
                "execution_status": execution_status,
                "block_reason_code": blocked.get("reason_code"),
                "block_reason_detail": blocked.get("details", {}),
                "price_snapshot_status": "stale" if bool(metadata.get("stale_quote")) else ("fallback" if metadata.get("routing_fallback") else "ok"),
            })
        planner_status = "ok" if items else "blocked"
        if summary.get("bridge_state") in {"planned_blocked", "planned_not_submitted"}:
            planner_status = "blocked"
        return {
            "status": "ok",
            "run_id": resolved_run_id,
            "cycle_id": summary.get("cycle_id"),
            "generated_at": plans[0].get("created_at") if plans else summary.get("last_transition_at"),
            "planner_status": planner_status,
            "reason_code": summary.get("zero_submit_reason_code") or summary.get("latest_reason_code"),
            "reason_summary": summary.get("zero_submit_reason_summary") or summary.get("latest_reason_summary"),
            "items": items,
        }
