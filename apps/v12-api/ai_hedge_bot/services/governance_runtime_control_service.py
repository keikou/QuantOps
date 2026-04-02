from __future__ import annotations

import json
from typing import Any

from ai_hedge_bot.app.container import CONTAINER
from ai_hedge_bot.core.clock import utc_now_iso
from ai_hedge_bot.core.ids import new_cycle_id
from ai_hedge_bot.repositories.audit_repository import AuditRepository
from ai_hedge_bot.repositories.sprint5_repository import Sprint5Repository
from ai_hedge_bot.services.runtime.runtime_service import RuntimeService


class GovernanceRuntimeControlService:
    DEGRADE_SLIPPAGE_BPS = 2.5
    BLOCK_SLIPPAGE_BPS = 4.0
    DEGRADE_LATENCY_MS = 25.0
    DEGRADE_EXECUTION_DRAG_USD = 3.0
    BLOCK_EXECUTION_DRAG_USD = 5.0
    SLIPPAGE_GUARD_PAUSE_BPS = 3.0
    SLIPPAGE_GUARD_HALT_BPS = 5.0
    THROTTLE_AVG_LATENCY_MS = 30.0
    STOP_AVG_LATENCY_MS = 50.0
    THROTTLE_P95_LATENCY_MS = 60.0
    STOP_P95_LATENCY_MS = 90.0
    TRIM_SYMBOL_DRAG_USD = 3.0
    ZERO_SYMBOL_DRAG_USD = 5.0
    TRIM_SYMBOL_NOTIONAL_SHARE = 0.3
    ZERO_SYMBOL_NOTIONAL_SHARE = 0.45
    ADAPTIVE_IMPROVEMENT_BPS = 1.0
    ADAPTIVE_WORSENING_BPS = 0.5
    RESOLUTION_PRIORITY = {
        "halt": 70,
        "stop": 60,
        "block": 50,
        "zero": 45,
        "pause": 40,
        "throttle": 30,
        "trim": 25,
        "degrade": 20,
        "allow": 10,
        "keep": 10,
        "continue": 10,
    }

    def __init__(self) -> None:
        self.repo = Sprint5Repository()
        self.runtime_service = RuntimeService()
        self.audit_repo = AuditRepository()

    @staticmethod
    def _decision_rank(decision: str) -> int:
        ranks = {
            "allow": 0,
            "degrade": 1,
            "block": 2,
        }
        return ranks.get(str(decision or "allow"), 0)

    def _latest_adaptive_route_feedback(self) -> dict[str, dict[str, Any]]:
        rows = self.audit_repo.list_logs(limit=500)
        feedback: dict[str, dict[str, Any]] = {}
        for row in rows:
            if str(row.get("category") or "") != "governance_runtime_control":
                continue
            if str(row.get("event_type") or "") != "adaptive_control_feedback":
                continue
            try:
                payload = json.loads(str(row.get("payload_json") or "{}"))
            except Exception:
                payload = {}
            if str(payload.get("control_family") or "") != "route_routing":
                continue
            route = str(payload.get("scope_key") or "")
            if route and route not in feedback:
                feedback[route] = {
                    **payload,
                    "created_at": row.get("created_at"),
                }
        return feedback

    def _latest_route_dominant_symbols(self, run_id: str | None) -> dict[str, str]:
        if not run_id:
            return {}
        rows = self.repo.store.fetchall_dict(
            """
            SELECT
                COALESCE(p.route, 'unknown') AS route,
                f.symbol AS symbol,
                SUM(ABS(COALESCE(f.fill_qty, 0.0) * COALESCE(f.fill_price, 0.0))) AS gross_notional_usd
            FROM execution_fills f
            LEFT JOIN execution_plans p
                ON p.plan_id = f.plan_id
            WHERE f.run_id = ?
            GROUP BY COALESCE(p.route, 'unknown'), f.symbol
            ORDER BY route ASC, gross_notional_usd DESC, symbol ASC
            """,
            [run_id],
        )
        route_symbols: dict[str, str] = {}
        for row in rows:
            route = str(row.get("route") or "")
            symbol = str(row.get("symbol") or "")
            if route and symbol and route not in route_symbols:
                route_symbols[route] = symbol
        return route_symbols

    @classmethod
    def _normalized_action(cls, decision: str) -> str:
        value = str(decision or "allow").lower()
        if value in cls.RESOLUTION_PRIORITY:
            return value
        return "allow"

    @classmethod
    def _precedence(cls, decision: str) -> int:
        return cls.RESOLUTION_PRIORITY.get(cls._normalized_action(decision), 0)

    def _resolution_source_packet(self, source: str) -> str:
        mapping = {
            "global_slippage_guard": "C2",
            "route_latency": "C3",
            "symbol_capital": "C4",
            "route_adaptive": "C5",
            "route_routing": "C1",
        }
        return mapping.get(source, "unknown")

    def routing_control_latest(self) -> dict[str, Any]:
        leakage = self.repo.latest_execution_route_leakage()
        items = list(leakage.get("items") or [])
        evaluated: list[dict[str, Any]] = []
        for item in items:
            avg_slippage_bps = float(item.get("avg_slippage_bps", 0.0) or 0.0)
            avg_latency_ms = float(item.get("avg_latency_ms", 0.0) or 0.0)
            execution_drag_usd = float(item.get("execution_drag_usd", 0.0) or 0.0)

            decision = "allow"
            reason = "within_limits"
            target_weight_multiplier = 1.0

            if avg_slippage_bps >= self.BLOCK_SLIPPAGE_BPS or execution_drag_usd >= self.BLOCK_EXECUTION_DRAG_USD:
                decision = "block"
                reason = "route_leakage_high"
                target_weight_multiplier = 0.0
            elif (
                avg_slippage_bps >= self.DEGRADE_SLIPPAGE_BPS
                or avg_latency_ms >= self.DEGRADE_LATENCY_MS
                or execution_drag_usd >= self.DEGRADE_EXECUTION_DRAG_USD
            ):
                decision = "degrade"
                reason = "route_leakage_elevated"
                target_weight_multiplier = 0.5

            evaluated.append(
                {
                    **item,
                    "decision": decision,
                    "reason": reason,
                    "target_weight_multiplier": target_weight_multiplier,
                }
            )

        return {
            "status": "ok",
            "run_id": leakage.get("run_id"),
            "mode": leakage.get("mode"),
            "items": evaluated,
            "decision_summary": {
                "allowed_routes": sum(1 for item in evaluated if item.get("decision") == "allow"),
                "degraded_routes": sum(1 for item in evaluated if item.get("decision") == "degrade"),
                "blocked_routes": sum(1 for item in evaluated if item.get("decision") == "block"),
            },
            "thresholds": {
                "degrade_slippage_bps": self.DEGRADE_SLIPPAGE_BPS,
                "block_slippage_bps": self.BLOCK_SLIPPAGE_BPS,
                "degrade_latency_ms": self.DEGRADE_LATENCY_MS,
                "degrade_execution_drag_usd": self.DEGRADE_EXECUTION_DRAG_USD,
                "block_execution_drag_usd": self.BLOCK_EXECUTION_DRAG_USD,
            },
            "as_of": leakage.get("as_of"),
        }

    def slippage_guard_latest(self) -> dict[str, Any]:
        quality = self.repo.latest_execution_quality_summary()
        trading_state = self.runtime_service.get_trading_state()
        avg_slippage_bps = float(quality.get("avg_slippage_bps", 0.0) or 0.0)

        decision = "continue"
        reason = "slippage_within_limits"
        target_trading_state = "running"
        severity = "info"

        if avg_slippage_bps >= self.SLIPPAGE_GUARD_HALT_BPS:
            decision = "halt"
            reason = "slippage_guard_critical"
            target_trading_state = "halted"
            severity = "critical"
        elif avg_slippage_bps >= self.SLIPPAGE_GUARD_PAUSE_BPS:
            decision = "pause"
            reason = "slippage_guard_elevated"
            target_trading_state = "paused"
            severity = "high"

        current_trading_state = str(trading_state.get("trading_state") or "running").lower()
        should_apply = target_trading_state != current_trading_state
        return {
            "status": "ok",
            "run_id": quality.get("run_id"),
            "cycle_id": quality.get("cycle_id"),
            "mode": quality.get("mode"),
            "avg_slippage_bps": avg_slippage_bps,
            "decision": decision,
            "reason": reason,
            "severity": severity,
            "current_trading_state": current_trading_state,
            "target_trading_state": target_trading_state,
            "should_apply": should_apply,
            "thresholds": {
                "pause_slippage_bps": self.SLIPPAGE_GUARD_PAUSE_BPS,
                "halt_slippage_bps": self.SLIPPAGE_GUARD_HALT_BPS,
            },
            "as_of": quality.get("as_of") or trading_state.get("as_of"),
        }

    def apply_slippage_guard_latest(self) -> dict[str, Any]:
        evaluation = self.slippage_guard_latest()
        decision = str(evaluation.get("decision") or "continue")

        if decision == "halt":
            applied = self.runtime_service.halt_trading(
                note=f"Slippage guard halt: avg_slippage_bps={evaluation.get('avg_slippage_bps')}",
                actor="governance_runtime_control",
            )
        elif decision == "pause":
            applied = self.runtime_service.pause_trading(
                note=f"Slippage guard pause: avg_slippage_bps={evaluation.get('avg_slippage_bps')}",
                actor="governance_runtime_control",
            )
        else:
            applied = self.runtime_service.get_trading_state()

        return {
            "status": "ok",
            "evaluation": evaluation,
            "applied_state": {
                "trading_state": applied.get("trading_state"),
                "note": applied.get("note"),
                "as_of": applied.get("as_of"),
                "cancelled_open_orders": int(applied.get("cancelled_open_orders", 0) or 0),
            },
        }

    def latency_throttle_latest(self) -> dict[str, Any]:
        quality = self.repo.latest_execution_quality_summary()
        run_id = quality.get("run_id")
        mode = quality.get("mode")
        cycle_id = quality.get("cycle_id")
        rows = list((self.repo.execution_latency_by_mode_route().get("items")) or [])
        scoped_rows = [
            row for row in rows
            if row.get("run_id") == run_id and row.get("mode") == mode
        ]

        evaluated: list[dict[str, Any]] = []
        for row in scoped_rows:
            avg_latency_ms = float(row.get("avg_latency_ms", 0.0) or 0.0)
            latency_ms_p95 = float(row.get("latency_ms_p95", 0.0) or 0.0)

            decision = "allow"
            reason = "latency_within_limits"
            participation_rate_multiplier = 1.0
            slice_interval_multiplier = 1.0

            if avg_latency_ms >= self.STOP_AVG_LATENCY_MS or latency_ms_p95 >= self.STOP_P95_LATENCY_MS:
                decision = "stop"
                reason = "latency_critical"
                participation_rate_multiplier = 0.0
                slice_interval_multiplier = 2.0
            elif avg_latency_ms >= self.THROTTLE_AVG_LATENCY_MS or latency_ms_p95 >= self.THROTTLE_P95_LATENCY_MS:
                decision = "throttle"
                reason = "latency_elevated"
                participation_rate_multiplier = 0.5
                slice_interval_multiplier = 1.5

            evaluated.append(
                {
                    **row,
                    "decision": decision,
                    "reason": reason,
                    "participation_rate_multiplier": participation_rate_multiplier,
                    "slice_interval_multiplier": slice_interval_multiplier,
                }
            )

        return {
            "status": "ok",
            "run_id": run_id,
            "cycle_id": cycle_id,
            "mode": mode,
            "items": evaluated,
            "decision_summary": {
                "allowed_routes": sum(1 for item in evaluated if item.get("decision") == "allow"),
                "throttled_routes": sum(1 for item in evaluated if item.get("decision") == "throttle"),
                "stopped_routes": sum(1 for item in evaluated if item.get("decision") == "stop"),
            },
            "thresholds": {
                "throttle_avg_latency_ms": self.THROTTLE_AVG_LATENCY_MS,
                "stop_avg_latency_ms": self.STOP_AVG_LATENCY_MS,
                "throttle_p95_latency_ms": self.THROTTLE_P95_LATENCY_MS,
                "stop_p95_latency_ms": self.STOP_P95_LATENCY_MS,
            },
            "as_of": quality.get("as_of"),
        }

    def symbol_capital_reallocation_latest(self) -> dict[str, Any]:
        leakage = self.repo.latest_execution_symbol_leakage()
        items = list(leakage.get("items") or [])
        evaluated: list[dict[str, Any]] = []
        for item in items:
            execution_drag_usd = float(item.get("execution_drag_usd", 0.0) or 0.0)
            notional_share = float(item.get("notional_share", 0.0) or 0.0)

            decision = "keep"
            reason = "symbol_drag_within_limits"
            target_capital_multiplier = 1.0

            if execution_drag_usd >= self.ZERO_SYMBOL_DRAG_USD or notional_share >= self.ZERO_SYMBOL_NOTIONAL_SHARE:
                decision = "zero"
                reason = "symbol_drag_critical"
                target_capital_multiplier = 0.0
            elif execution_drag_usd >= self.TRIM_SYMBOL_DRAG_USD or notional_share >= self.TRIM_SYMBOL_NOTIONAL_SHARE:
                decision = "trim"
                reason = "symbol_drag_elevated"
                target_capital_multiplier = 0.5

            evaluated.append(
                {
                    **item,
                    "decision": decision,
                    "reason": reason,
                    "target_capital_multiplier": target_capital_multiplier,
                }
            )

        return {
            "status": "ok",
            "run_id": leakage.get("run_id"),
            "mode": leakage.get("mode"),
            "items": evaluated,
            "decision_summary": {
                "kept_symbols": sum(1 for item in evaluated if item.get("decision") == "keep"),
                "trimmed_symbols": sum(1 for item in evaluated if item.get("decision") == "trim"),
                "zeroed_symbols": sum(1 for item in evaluated if item.get("decision") == "zero"),
            },
            "thresholds": {
                "trim_symbol_drag_usd": self.TRIM_SYMBOL_DRAG_USD,
                "zero_symbol_drag_usd": self.ZERO_SYMBOL_DRAG_USD,
                "trim_symbol_notional_share": self.TRIM_SYMBOL_NOTIONAL_SHARE,
                "zero_symbol_notional_share": self.ZERO_SYMBOL_NOTIONAL_SHARE,
            },
            "as_of": leakage.get("as_of"),
        }

    def closed_loop_adaptive_control_latest(self) -> dict[str, Any]:
        routing = self.routing_control_latest()
        previous_feedback = self._latest_adaptive_route_feedback()
        evaluated: list[dict[str, Any]] = []
        for item in list(routing.get("items") or []):
            route = str(item.get("route") or "")
            previous = previous_feedback.get(route) or {}
            base_decision = str(item.get("decision") or "allow")
            adapted_decision = base_decision
            adaptation_state = "cold_start"
            cooldown_active = False
            previous_run_id = str(previous.get("run_id") or "")
            current_run_id = str(routing.get("run_id") or "")
            current_slippage_bps = float(item.get("avg_slippage_bps", 0.0) or 0.0)
            previous_slippage_bps = float(previous.get("observed_slippage_bps", current_slippage_bps) or current_slippage_bps)
            delta_slippage_bps = round(current_slippage_bps - previous_slippage_bps, 6)

            if previous:
                adaptation_state = "held"
                previous_decision = str(previous.get("adapted_decision") or previous.get("base_decision") or "allow")
                if previous_run_id == current_run_id:
                    cooldown_active = True
                    adaptation_state = "cooldown_hold"
                    adapted_decision = previous_decision
                elif (
                    previous_decision == "degrade"
                    and base_decision == "allow"
                    and delta_slippage_bps <= -self.ADAPTIVE_IMPROVEMENT_BPS
                ):
                    adapted_decision = "allow"
                    adaptation_state = "relax_after_improvement"
                elif (
                    previous_decision == "block"
                    and base_decision == "degrade"
                    and delta_slippage_bps <= -self.ADAPTIVE_IMPROVEMENT_BPS
                ):
                    adapted_decision = "degrade"
                    adaptation_state = "relax_after_improvement"
                elif (
                    previous_decision == "degrade"
                    and base_decision == "degrade"
                    and delta_slippage_bps >= self.ADAPTIVE_WORSENING_BPS
                ):
                    adapted_decision = "block"
                    adaptation_state = "escalate_after_failed_degrade"
                elif (
                    previous_decision == "allow"
                    and self._decision_rank(base_decision) > self._decision_rank(previous_decision)
                ):
                    adapted_decision = base_decision
                    adaptation_state = "escalate_from_current_signal"
                else:
                    adapted_decision = base_decision

            target_weight_multiplier = float(item.get("target_weight_multiplier", 1.0) or 1.0)
            if adapted_decision == "block":
                adaptive_target_weight_multiplier = 0.0
            elif adapted_decision == "degrade":
                adaptive_target_weight_multiplier = min(target_weight_multiplier, 0.5)
            else:
                adaptive_target_weight_multiplier = 1.0

            evaluated.append(
                {
                    **item,
                    "base_decision": base_decision,
                    "adapted_decision": adapted_decision,
                    "adaptation_state": adaptation_state,
                    "cooldown_active": cooldown_active,
                    "previous_run_id": previous_run_id or None,
                    "previous_decision": previous.get("adapted_decision") or previous.get("base_decision"),
                    "previous_observed_slippage_bps": previous.get("observed_slippage_bps"),
                    "delta_slippage_bps": delta_slippage_bps,
                    "adaptive_target_weight_multiplier": adaptive_target_weight_multiplier,
                }
            )

        return {
            "status": "ok",
            "run_id": routing.get("run_id"),
            "mode": routing.get("mode"),
            "items": evaluated,
            "decision_summary": {
                "cold_start_routes": sum(1 for item in evaluated if item.get("adaptation_state") == "cold_start"),
                "adapted_routes": sum(1 for item in evaluated if str(item.get("adaptation_state")) not in {"cold_start", "held", "cooldown_hold"}),
                "cooldown_routes": sum(1 for item in evaluated if item.get("cooldown_active")),
                "blocked_routes": sum(1 for item in evaluated if item.get("adapted_decision") == "block"),
            },
            "thresholds": {
                "improvement_bps": self.ADAPTIVE_IMPROVEMENT_BPS,
                "worsening_bps": self.ADAPTIVE_WORSENING_BPS,
            },
            "as_of": routing.get("as_of"),
        }

    def apply_closed_loop_adaptive_control_latest(self) -> dict[str, Any]:
        evaluation = self.closed_loop_adaptive_control_latest()
        created_at = utc_now_iso()
        for item in list(evaluation.get("items") or []):
            payload = {
                "control_family": "route_routing",
                "scope_key": item.get("route"),
                "run_id": evaluation.get("run_id"),
                "mode": evaluation.get("mode"),
                "base_decision": item.get("base_decision"),
                "adapted_decision": item.get("adapted_decision"),
                "observed_slippage_bps": item.get("avg_slippage_bps"),
                "delta_slippage_bps": item.get("delta_slippage_bps"),
                "adaptation_state": item.get("adaptation_state"),
                "cooldown_active": bool(item.get("cooldown_active")),
                "adaptive_target_weight_multiplier": item.get("adaptive_target_weight_multiplier"),
            }
            self.audit_repo.create_log(
                {
                    "audit_id": new_cycle_id(),
                    "category": "governance_runtime_control",
                    "event_type": "adaptive_control_feedback",
                    "run_id": evaluation.get("run_id"),
                    "created_at": created_at,
                    "payload_json": CONTAINER.runtime_store.to_json(payload),
                    "actor": "governance_runtime_control",
                }
            )
        return {
            "status": "ok",
            "saved_feedback_count": len(list(evaluation.get("items") or [])),
            "evaluation": evaluation,
        }

    def cross_control_policy_arbitration_latest(self) -> dict[str, Any]:
        routing = self.routing_control_latest()
        slippage_guard = self.slippage_guard_latest()
        latency = self.latency_throttle_latest()
        symbol_reallocation = self.symbol_capital_reallocation_latest()
        adaptive = self.closed_loop_adaptive_control_latest()

        run_id = routing.get("run_id") or adaptive.get("run_id")
        mode = routing.get("mode") or adaptive.get("mode")
        cycle_id = slippage_guard.get("cycle_id")
        route_to_symbol = self._latest_route_dominant_symbols(str(run_id or ""))
        route_rows = {str(item.get("route") or ""): item for item in list(routing.get("items") or [])}
        latency_rows = {str(item.get("route") or ""): item for item in list(latency.get("items") or [])}
        adaptive_rows = {str(item.get("route") or ""): item for item in list(adaptive.get("items") or [])}
        symbol_rows = {str(item.get("symbol") or ""): item for item in list(symbol_reallocation.get("items") or [])}
        routes = sorted(set(route_rows) | set(latency_rows) | set(adaptive_rows))

        resolved_items: list[dict[str, Any]] = []
        for route in routes:
            dominant_symbol = route_to_symbol.get(route)
            route_row = route_rows.get(route) or {}
            latency_row = latency_rows.get(route) or {}
            adaptive_row = adaptive_rows.get(route) or {}
            symbol_row = symbol_rows.get(str(dominant_symbol or "")) or {}

            candidates = [
                {
                    "source": "global_slippage_guard",
                    "decision": slippage_guard.get("decision"),
                    "reason": slippage_guard.get("reason"),
                    "scope": "global",
                },
                {
                    "source": "route_latency",
                    "decision": latency_row.get("decision"),
                    "reason": latency_row.get("reason"),
                    "scope": "route",
                },
                {
                    "source": "symbol_capital",
                    "decision": symbol_row.get("decision"),
                    "reason": symbol_row.get("reason"),
                    "scope": "symbol",
                },
                {
                    "source": "route_adaptive",
                    "decision": adaptive_row.get("adapted_decision"),
                    "reason": adaptive_row.get("adaptation_state"),
                    "scope": "route",
                },
                {
                    "source": "route_routing",
                    "decision": route_row.get("decision"),
                    "reason": route_row.get("reason"),
                    "scope": "route",
                },
            ]
            valid_candidates = [item for item in candidates if item.get("decision") is not None]
            sorted_candidates = sorted(
                valid_candidates,
                key=lambda item: (
                    -self._precedence(str(item.get("decision") or "")),
                    self._resolution_source_packet(str(item.get("source") or "")),
                ),
            )
            winner = sorted_candidates[0] if sorted_candidates else {
                "source": "route_routing",
                "decision": "allow",
                "reason": "no_control_signal",
                "scope": "route",
            }
            distinct_actions = sorted({self._normalized_action(str(item.get("decision") or "")) for item in valid_candidates})
            conflicts = []
            if len(distinct_actions) > 1:
                for item in valid_candidates:
                    conflicts.append(
                        {
                            "source": item.get("source"),
                            "decision": self._normalized_action(str(item.get("decision") or "")),
                            "reason": item.get("reason"),
                        }
                    )

            resolved_items.append(
                {
                    "route": route,
                    "symbol": dominant_symbol,
                    "resolved_runtime_action": self._normalized_action(str(winner.get("decision") or "")),
                    "resolved_reason_set": [str(item.get("reason") or "") for item in valid_candidates if item.get("reason")],
                    "resolved_scope": "global" if winner.get("source") == "global_slippage_guard" else ("symbol" if winner.get("source") == "symbol_capital" else "route"),
                    "resolution_source_packet": self._resolution_source_packet(str(winner.get("source") or "")),
                    "resolution_source": winner.get("source"),
                    "raw_controls": {
                        "route_routing": route_row.get("decision"),
                        "global_slippage_guard": slippage_guard.get("decision"),
                        "route_latency": latency_row.get("decision"),
                        "symbol_capital": symbol_row.get("decision"),
                        "route_adaptive": adaptive_row.get("adapted_decision"),
                    },
                    "conflicts": conflicts,
                    "has_conflict": bool(conflicts),
                    "cooldown_active": bool(adaptive_row.get("cooldown_active")),
                }
            )

        return {
            "status": "ok",
            "run_id": run_id,
            "cycle_id": cycle_id,
            "mode": mode,
            "items": resolved_items,
            "decision_summary": {
                "route_count": len(resolved_items),
                "conflicted_routes": sum(1 for item in resolved_items if item.get("has_conflict")),
                "global_halt_routes": sum(1 for item in resolved_items if item.get("resolved_runtime_action") == "halt"),
                "blocking_routes": sum(1 for item in resolved_items if item.get("resolved_runtime_action") in {"stop", "block", "zero"}),
            },
            "precedence_order": [
                "halt",
                "stop",
                "block",
                "zero",
                "pause",
                "throttle",
                "trim",
                "degrade",
                "allow",
                "keep",
                "continue",
            ],
            "as_of": adaptive.get("as_of") or routing.get("as_of"),
        }

    def apply_cross_control_policy_arbitration_latest(self) -> dict[str, Any]:
        evaluation = self.cross_control_policy_arbitration_latest()
        created_at = utc_now_iso()
        for item in list(evaluation.get("items") or []):
            self.audit_repo.create_log(
                {
                    "audit_id": new_cycle_id(),
                    "category": "governance_runtime_control",
                    "event_type": "policy_arbitration_resolution",
                    "run_id": evaluation.get("run_id"),
                    "created_at": created_at,
                    "payload_json": CONTAINER.runtime_store.to_json(item),
                    "actor": "governance_runtime_control",
                }
            )
        return {
            "status": "ok",
            "saved_resolution_count": len(list(evaluation.get("items") or [])),
            "evaluation": evaluation,
        }
