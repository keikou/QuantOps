from __future__ import annotations

from typing import Any

from ai_hedge_bot.repositories.sprint5_repository import Sprint5Repository
from ai_hedge_bot.services.governance_runtime_control_service import GovernanceRuntimeControlService


class PortfolioIntelligenceService:
    STABILITY_CHANGE_THRESHOLD = 0.05
    TRADEOFF_INCREASE_THRESHOLD = 0.45
    TRADEOFF_HOLD_THRESHOLD = 0.2
    CONCENTRATION_SOFT_LIMIT = 0.35
    OUTCOME_IMPROVEMENT_EPSILON = 1e-6

    def __init__(self) -> None:
        self.repo = Sprint5Repository()
        self.governance = GovernanceRuntimeControlService()

    @staticmethod
    def _clamp(value: float, lower: float = 0.0, upper: float = 1.0) -> float:
        return max(lower, min(upper, value))

    def _latest_symbol_routes(self, run_id: str | None) -> dict[str, str]:
        if not run_id:
            return {}
        rows = self.repo.store.fetchall_dict(
            """
            SELECT
                f.symbol AS symbol,
                COALESCE(p.route, 'unknown') AS route,
                SUM(ABS(COALESCE(f.fill_qty, 0.0) * COALESCE(f.fill_price, 0.0))) AS gross_notional_usd
            FROM execution_fills f
            LEFT JOIN execution_plans p
                ON p.plan_id = f.plan_id
            WHERE f.run_id = ?
            GROUP BY f.symbol, COALESCE(p.route, 'unknown')
            ORDER BY symbol ASC, gross_notional_usd DESC, route ASC
            """,
            [run_id],
        )
        symbol_routes: dict[str, str] = {}
        for row in rows:
            symbol = str(row.get("symbol") or "")
            route = str(row.get("route") or "")
            if symbol and route and symbol not in symbol_routes:
                symbol_routes[symbol] = route
        return symbol_routes

    def _execution_quality_by_run(self, run_id: str | None) -> dict[str, Any]:
        if not run_id:
            return {"status": "ok", "run_id": None, "cycle_id": None, "mode": None}
        row = self.repo.store.fetchone_dict(
            """
            SELECT snapshot_id, created_at, run_id, cycle_id, mode, order_count, fill_count, fill_rate,
                   avg_slippage_bps, latency_ms_p50, latency_ms_p95
            FROM execution_quality_snapshots
            WHERE run_id = ?
            ORDER BY created_at DESC
            LIMIT 1
            """,
            [run_id],
        ) or {}
        if not row:
            return {"status": "ok", "run_id": None, "cycle_id": None, "mode": None}
        payload = dict(row)
        payload["status"] = "ok"
        payload["as_of"] = row.get("created_at")
        return payload

    def _execution_drag_by_run(self, run_id: str | None) -> dict[str, Any]:
        if not run_id:
            return {"status": "ok", "run_id": None, "drag": {}}
        row = self.repo.store.fetchone_dict(
            """
            SELECT run_id, created_at, gross_alpha_pnl_usd, net_shadow_pnl_usd,
                   execution_drag_usd, slippage_drag_usd, fee_drag_usd, latency_drag_usd
            FROM shadow_pnl_snapshots
            WHERE run_id = ?
            ORDER BY created_at DESC
            LIMIT 1
            """,
            [run_id],
        ) or {}
        if not row:
            return {"status": "ok", "run_id": run_id, "drag": {}}
        return {
            "status": "ok",
            "run_id": run_id,
            "as_of": row.get("created_at"),
            "drag": {
                "gross_alpha_pnl_usd": float(row.get("gross_alpha_pnl_usd", 0.0) or 0.0),
                "net_shadow_pnl_usd": float(row.get("net_shadow_pnl_usd", 0.0) or 0.0),
                "execution_drag_usd": float(row.get("execution_drag_usd", 0.0) or 0.0),
                "slippage_drag_usd": float(row.get("slippage_drag_usd", 0.0) or 0.0),
                "fee_drag_usd": float(row.get("fee_drag_usd", 0.0) or 0.0),
                "latency_drag_usd": float(row.get("latency_drag_usd", 0.0) or 0.0),
            },
        }

    def _symbol_leakage_by_run(self, run_id: str | None) -> dict[str, Any]:
        drag_payload = self._execution_drag_by_run(run_id)
        drag = dict(drag_payload.get("drag") or {})
        quality = self._execution_quality_by_run(run_id)
        fills = self.repo.store.fetchall_dict(
            """
            SELECT symbol, fill_qty, fill_price, slippage_bps, latency_ms, fee_bps
            FROM execution_fills
            WHERE run_id = ?
            ORDER BY symbol ASC
            """,
            [run_id],
        ) if run_id else []
        symbol_rows: dict[str, dict[str, Any]] = {}
        total_notional = 0.0
        for fill in fills:
            symbol = str(fill.get("symbol") or "unknown")
            qty = abs(float(fill.get("fill_qty", 0.0) or 0.0))
            price = float(fill.get("fill_price", 0.0) or 0.0)
            notional = qty * price
            total_notional += notional
            row = symbol_rows.setdefault(
                symbol,
                {
                    "symbol": symbol,
                    "fill_count": 0,
                    "gross_notional_usd": 0.0,
                    "avg_slippage_bps": 0.0,
                    "avg_latency_ms": 0.0,
                    "avg_fee_bps": 0.0,
                },
            )
            row["fill_count"] += 1
            row["gross_notional_usd"] += notional
            row["avg_slippage_bps"] += float(fill.get("slippage_bps", 0.0) or 0.0)
            row["avg_latency_ms"] += float(fill.get("latency_ms", 0.0) or 0.0)
            row["avg_fee_bps"] += float(fill.get("fee_bps", 0.0) or 0.0)
        items: list[dict[str, Any]] = []
        total_slippage_drag = float(drag.get("slippage_drag_usd", 0.0) or 0.0)
        total_fee_drag = float(drag.get("fee_drag_usd", 0.0) or 0.0)
        total_latency_drag = float(drag.get("latency_drag_usd", 0.0) or 0.0)
        total_execution_drag = float(drag.get("execution_drag_usd", 0.0) or 0.0)
        for symbol in sorted(symbol_rows):
            row = symbol_rows[symbol]
            fill_count = max(int(row["fill_count"]), 1)
            row["avg_slippage_bps"] = float(row["avg_slippage_bps"]) / fill_count
            row["avg_latency_ms"] = float(row["avg_latency_ms"]) / fill_count
            row["avg_fee_bps"] = float(row["avg_fee_bps"]) / fill_count
            share = float(row["gross_notional_usd"]) / total_notional if total_notional > 1e-9 else 0.0
            row["notional_share"] = share
            row["slippage_drag_usd"] = round(total_slippage_drag * share, 8)
            row["fee_drag_usd"] = round(total_fee_drag * share, 8)
            row["latency_drag_usd"] = round(total_latency_drag * share, 8)
            row["execution_drag_usd"] = round(total_execution_drag * share, 8)
            items.append(row)
        return {
            "status": "ok",
            "run_id": run_id,
            "mode": quality.get("mode"),
            "items": items,
            "as_of": quality.get("as_of") or drag_payload.get("as_of"),
        }

    def _route_leakage_by_run(self, run_id: str | None) -> dict[str, Any]:
        drag_payload = self._execution_drag_by_run(run_id)
        drag = dict(drag_payload.get("drag") or {})
        quality = self._execution_quality_by_run(run_id)
        fills = self.repo.store.fetchall_dict(
            """
            SELECT f.symbol, f.fill_qty, f.fill_price, f.slippage_bps, f.latency_ms, f.fee_bps,
                   COALESCE(p.route, 'unknown') AS route
            FROM execution_fills f
            LEFT JOIN execution_plans p
                ON p.plan_id = f.plan_id
            WHERE f.run_id = ?
            ORDER BY route ASC, f.symbol ASC
            """,
            [run_id],
        ) if run_id else []
        route_rows: dict[str, dict[str, Any]] = {}
        total_notional = 0.0
        for fill in fills:
            route = str(fill.get("route") or "unknown")
            qty = abs(float(fill.get("fill_qty", 0.0) or 0.0))
            price = float(fill.get("fill_price", 0.0) or 0.0)
            notional = qty * price
            total_notional += notional
            row = route_rows.setdefault(
                route,
                {
                    "route": route,
                    "fill_count": 0,
                    "gross_notional_usd": 0.0,
                    "avg_slippage_bps": 0.0,
                    "avg_latency_ms": 0.0,
                    "avg_fee_bps": 0.0,
                },
            )
            row["fill_count"] += 1
            row["gross_notional_usd"] += notional
            row["avg_slippage_bps"] += float(fill.get("slippage_bps", 0.0) or 0.0)
            row["avg_latency_ms"] += float(fill.get("latency_ms", 0.0) or 0.0)
            row["avg_fee_bps"] += float(fill.get("fee_bps", 0.0) or 0.0)
        items: list[dict[str, Any]] = []
        total_slippage_drag = float(drag.get("slippage_drag_usd", 0.0) or 0.0)
        total_fee_drag = float(drag.get("fee_drag_usd", 0.0) or 0.0)
        total_latency_drag = float(drag.get("latency_drag_usd", 0.0) or 0.0)
        total_execution_drag = float(drag.get("execution_drag_usd", 0.0) or 0.0)
        for route in sorted(route_rows):
            row = route_rows[route]
            fill_count = max(int(row["fill_count"]), 1)
            row["avg_slippage_bps"] = float(row["avg_slippage_bps"]) / fill_count
            row["avg_latency_ms"] = float(row["avg_latency_ms"]) / fill_count
            row["avg_fee_bps"] = float(row["avg_fee_bps"]) / fill_count
            share = float(row["gross_notional_usd"]) / total_notional if total_notional > 1e-9 else 0.0
            row["notional_share"] = share
            row["slippage_drag_usd"] = round(total_slippage_drag * share, 8)
            row["fee_drag_usd"] = round(total_fee_drag * share, 8)
            row["latency_drag_usd"] = round(total_latency_drag * share, 8)
            row["execution_drag_usd"] = round(total_execution_drag * share, 8)
            items.append(row)
        return {
            "status": "ok",
            "run_id": run_id,
            "mode": quality.get("mode"),
            "items": items,
            "as_of": quality.get("as_of") or drag_payload.get("as_of"),
        }

    def _latency_by_route_for_run(self, run_id: str | None) -> dict[str, Any]:
        quality = self._execution_quality_by_run(run_id)
        mode = quality.get("mode")
        cycle_id = quality.get("cycle_id")
        rows = self.repo.store.fetchall_dict(
            """
            SELECT COALESCE(p.route, 'unknown') AS route,
                   COUNT(*) AS fill_count,
                   AVG(COALESCE(f.latency_ms, 0.0)) AS avg_latency_ms,
                   MIN(COALESCE(f.latency_ms, 0.0)) AS latency_ms_p50,
                   MAX(COALESCE(f.latency_ms, 0.0)) AS latency_ms_p95
            FROM execution_fills f
            LEFT JOIN execution_plans p
                ON p.plan_id = f.plan_id
            WHERE f.run_id = ?
            GROUP BY COALESCE(p.route, 'unknown')
            ORDER BY route ASC
            """,
            [run_id],
        ) if run_id else []
        return {
            "status": "ok",
            "run_id": run_id,
            "cycle_id": cycle_id,
            "mode": mode,
            "items": [
                {
                    "route": str(row.get("route") or "unknown"),
                    "fill_count": int(row.get("fill_count", 0) or 0),
                    "avg_latency_ms": float(row.get("avg_latency_ms", 0.0) or 0.0),
                    "latency_ms_p50": float(row.get("latency_ms_p50", 0.0) or 0.0),
                    "latency_ms_p95": float(row.get("latency_ms_p95", 0.0) or 0.0),
                }
                for row in rows
            ],
            "as_of": quality.get("as_of"),
        }

    def _execution_aware_capital_allocation_for_run(self, run_id: str | None) -> dict[str, Any]:
        overview = self.repo.latest_portfolio_overview()
        symbol_leakage = self._symbol_leakage_by_run(run_id)
        route_leakage = self._route_leakage_by_run(run_id)
        latency = self._latency_by_route_for_run(run_id)
        quality = self._execution_quality_by_run(run_id)

        summary = dict(overview.get("summary") or {})
        positions = list(overview.get("positions") or [])
        total_equity = float(summary.get("total_equity", 0.0) or 0.0)
        equity_denom = max(abs(total_equity), 1e-9)
        mode = quality.get("mode")
        cycle_id = quality.get("cycle_id")
        global_guard_decision = (
            "halt" if float(quality.get("avg_slippage_bps", 0.0) or 0.0) >= self.governance.SLIPPAGE_GUARD_HALT_BPS
            else "pause" if float(quality.get("avg_slippage_bps", 0.0) or 0.0) >= self.governance.SLIPPAGE_GUARD_PAUSE_BPS
            else "continue"
        )

        position_rows = {str(row.get("symbol") or ""): row for row in positions}
        leakage_rows = {str(row.get("symbol") or ""): row for row in list(symbol_leakage.get("items") or [])}
        route_rows = {str(row.get("route") or ""): row for row in list(route_leakage.get("items") or [])}
        latency_rows = {str(row.get("route") or ""): row for row in list(latency.get("items") or [])}
        symbol_routes = self._latest_symbol_routes(str(run_id or ""))

        symbols = sorted(set(position_rows) | set(leakage_rows))
        items: list[dict[str, Any]] = []
        for symbol in symbols:
            position = position_rows.get(symbol) or {}
            leakage = leakage_rows.get(symbol) or {}
            route = symbol_routes.get(symbol)
            route_row = route_rows.get(str(route or "")) or {}
            latency_row = latency_rows.get(str(route or "")) or {}
            exposure_notional = float(position.get("exposure_notional", 0.0) or 0.0)
            current_weight = exposure_notional / equity_denom if exposure_notional else 0.0

            resolved_control_action = "allow"
            symbol_control_decision = "keep"
            if float(leakage.get("execution_drag_usd", 0.0) or 0.0) >= self.governance.ZERO_SYMBOL_DRAG_USD or float(leakage.get("notional_share", 0.0) or 0.0) >= self.governance.ZERO_SYMBOL_NOTIONAL_SHARE:
                symbol_control_decision = "zero"
            elif float(leakage.get("execution_drag_usd", 0.0) or 0.0) >= self.governance.TRIM_SYMBOL_DRAG_USD or float(leakage.get("notional_share", 0.0) or 0.0) >= self.governance.TRIM_SYMBOL_NOTIONAL_SHARE:
                symbol_control_decision = "trim"

            if float(latency_row.get("avg_latency_ms", 0.0) or 0.0) >= self.governance.STOP_AVG_LATENCY_MS or float(latency_row.get("latency_ms_p95", 0.0) or 0.0) >= self.governance.STOP_P95_LATENCY_MS:
                resolved_control_action = "stop"
            elif float(latency_row.get("avg_latency_ms", 0.0) or 0.0) >= self.governance.THROTTLE_AVG_LATENCY_MS or float(latency_row.get("latency_ms_p95", 0.0) or 0.0) >= self.governance.THROTTLE_P95_LATENCY_MS:
                resolved_control_action = "throttle"
            elif float(route_row.get("avg_slippage_bps", 0.0) or 0.0) >= self.governance.DEGRADE_SLIPPAGE_BPS:
                resolved_control_action = "degrade"

            allocation_decision = "keep"
            target_capital_multiplier = 1.0
            winning_source = "none"
            reason = "within_limits"
            if global_guard_decision == "halt":
                allocation_decision = "zero"
                target_capital_multiplier = 0.0
                winning_source = "global_guard"
                reason = "global_guard_halt"
            elif global_guard_decision == "pause":
                allocation_decision = "trim"
                target_capital_multiplier = 0.25
                winning_source = "global_guard"
                reason = "global_guard_pause"
            elif resolved_control_action in {"stop", "block", "zero"}:
                allocation_decision = "zero"
                target_capital_multiplier = 0.0
                winning_source = "resolved_control"
                reason = f"resolved_control_{resolved_control_action}"
            elif symbol_control_decision == "zero":
                allocation_decision = "zero"
                target_capital_multiplier = 0.0
                winning_source = "symbol_control"
                reason = "symbol_control_zero"
            elif resolved_control_action in {"throttle", "trim"}:
                allocation_decision = "trim"
                target_capital_multiplier = 0.5
                winning_source = "resolved_control"
                reason = f"resolved_control_{resolved_control_action}"
            elif symbol_control_decision == "trim":
                allocation_decision = "trim"
                target_capital_multiplier = 0.5
                winning_source = "symbol_control"
                reason = "symbol_control_trim"
            elif resolved_control_action in {"degrade", "pause"}:
                allocation_decision = "trim"
                target_capital_multiplier = 0.75
                winning_source = "resolved_control"
                reason = f"resolved_control_{resolved_control_action}"

            items.append(
                {
                    "symbol": symbol,
                    "route": route,
                    "current_weight": round(current_weight, 6),
                    "current_notional_usd": round(exposure_notional, 6),
                    "execution_drag_usd": float(leakage.get("execution_drag_usd", 0.0) or 0.0),
                    "notional_share": float(leakage.get("notional_share", 0.0) or 0.0),
                    "avg_slippage_bps": float(leakage.get("avg_slippage_bps", 0.0) or 0.0),
                    "symbol_control_decision": symbol_control_decision,
                    "resolved_control_action": resolved_control_action,
                    "resolved_control_source_packet": None,
                    "global_guard_decision": global_guard_decision,
                    "allocation_decision": allocation_decision,
                    "target_capital_multiplier": target_capital_multiplier,
                    "winning_source": winning_source,
                    "decision_reason": reason,
                }
            )

        return {
            "status": "ok",
            "run_id": run_id,
            "cycle_id": cycle_id,
            "mode": mode,
            "total_equity": total_equity,
            "global_guard_decision": global_guard_decision,
            "items": items,
            "decision_summary": {
                "symbol_count": len(items),
            },
            "as_of": quality.get("as_of") or summary.get("as_of"),
        }

    def execution_aware_capital_allocation_latest(self) -> dict[str, Any]:
        overview = self.repo.latest_portfolio_overview()
        symbol_leakage = self.repo.latest_execution_symbol_leakage()
        symbol_control = self.governance.symbol_capital_reallocation_latest()
        arbitration = self.governance.cross_control_policy_arbitration_latest()
        slippage_guard = self.governance.slippage_guard_latest()

        summary = dict(overview.get("summary") or {})
        positions = list(overview.get("positions") or [])
        total_equity = float(summary.get("total_equity", 0.0) or 0.0)
        equity_denom = max(abs(total_equity), 1e-9)
        run_id = (
            symbol_leakage.get("run_id")
            or arbitration.get("run_id")
            or (overview.get("snapshot") or {}).get("run_id")
        )
        mode = symbol_leakage.get("mode") or arbitration.get("mode")
        cycle_id = arbitration.get("cycle_id")

        position_rows = {str(row.get("symbol") or ""): row for row in positions}
        leakage_rows = {str(row.get("symbol") or ""): row for row in list(symbol_leakage.get("items") or [])}
        symbol_control_rows = {str(row.get("symbol") or ""): row for row in list(symbol_control.get("items") or [])}
        route_resolution_rows = {str(row.get("route") or ""): row for row in list(arbitration.get("items") or [])}
        symbol_routes = self._latest_symbol_routes(str(run_id or ""))

        symbols = sorted(set(position_rows) | set(leakage_rows) | set(symbol_control_rows))
        items: list[dict[str, Any]] = []
        global_guard_decision = str(slippage_guard.get("decision") or "continue")

        for symbol in symbols:
            position = position_rows.get(symbol) or {}
            leakage = leakage_rows.get(symbol) or {}
            symbol_decision_row = symbol_control_rows.get(symbol) or {}
            route = symbol_routes.get(symbol)
            route_resolution = route_resolution_rows.get(str(route or "")) or {}
            exposure_notional = float(position.get("exposure_notional", 0.0) or 0.0)
            current_weight = exposure_notional / equity_denom if exposure_notional else 0.0

            allocation_decision = "keep"
            target_capital_multiplier = 1.0
            winning_source = "none"
            reason = "within_limits"

            resolved_control_action = str(route_resolution.get("resolved_runtime_action") or "allow")
            symbol_control_decision = str(symbol_decision_row.get("decision") or "keep")

            if global_guard_decision == "halt":
                allocation_decision = "zero"
                target_capital_multiplier = 0.0
                winning_source = "global_guard"
                reason = "global_guard_halt"
            elif global_guard_decision == "pause":
                allocation_decision = "trim"
                target_capital_multiplier = 0.25
                winning_source = "global_guard"
                reason = "global_guard_pause"
            elif resolved_control_action in {"stop", "block", "zero"}:
                allocation_decision = "zero"
                target_capital_multiplier = 0.0
                winning_source = "resolved_control"
                reason = f"resolved_control_{resolved_control_action}"
            elif symbol_control_decision == "zero":
                allocation_decision = "zero"
                target_capital_multiplier = 0.0
                winning_source = "symbol_control"
                reason = "symbol_control_zero"
            elif resolved_control_action in {"throttle", "trim"}:
                allocation_decision = "trim"
                target_capital_multiplier = 0.5
                winning_source = "resolved_control"
                reason = f"resolved_control_{resolved_control_action}"
            elif symbol_control_decision == "trim":
                allocation_decision = "trim"
                target_capital_multiplier = 0.5
                winning_source = "symbol_control"
                reason = "symbol_control_trim"
            elif resolved_control_action in {"degrade", "pause"}:
                allocation_decision = "trim"
                target_capital_multiplier = 0.75
                winning_source = "resolved_control"
                reason = f"resolved_control_{resolved_control_action}"

            items.append(
                {
                    "symbol": symbol,
                    "route": route,
                    "current_weight": round(current_weight, 6),
                    "current_notional_usd": round(exposure_notional, 6),
                    "execution_drag_usd": float(leakage.get("execution_drag_usd", 0.0) or 0.0),
                    "notional_share": float(leakage.get("notional_share", 0.0) or 0.0),
                    "avg_slippage_bps": float(leakage.get("avg_slippage_bps", 0.0) or 0.0),
                    "symbol_control_decision": symbol_control_decision,
                    "resolved_control_action": resolved_control_action,
                    "resolved_control_source_packet": route_resolution.get("resolution_source_packet"),
                    "global_guard_decision": global_guard_decision,
                    "allocation_decision": allocation_decision,
                    "target_capital_multiplier": target_capital_multiplier,
                    "winning_source": winning_source,
                    "decision_reason": reason,
                }
            )

        return {
            "status": "ok",
            "run_id": run_id,
            "cycle_id": cycle_id,
            "mode": mode,
            "total_equity": total_equity,
            "global_guard_decision": global_guard_decision,
            "items": items,
            "decision_summary": {
                "symbol_count": len(items),
                "keep_symbols": sum(1 for item in items if item.get("allocation_decision") == "keep"),
                "trim_symbols": sum(1 for item in items if item.get("allocation_decision") == "trim"),
                "zero_symbols": sum(1 for item in items if item.get("allocation_decision") == "zero"),
            },
            "as_of": (
                slippage_guard.get("as_of")
                or symbol_leakage.get("as_of")
                or summary.get("as_of")
                or (overview.get("snapshot") or {}).get("created_at")
            ),
        }

    def execution_aware_exposure_shaping_latest(self) -> dict[str, Any]:
        allocation = self.execution_aware_capital_allocation_latest()
        items = list(allocation.get("items") or [])
        shaped_items: list[dict[str, Any]] = []
        gross_target = 0.0
        net_target = 0.0

        for item in items:
            current_weight = float(item.get("current_weight", 0.0) or 0.0)
            multiplier = float(item.get("target_capital_multiplier", 0.0) or 0.0)
            target_weight = round(current_weight * multiplier, 6)
            gross_target += abs(target_weight)
            net_target += target_weight
            shaped_items.append(
                {
                    **item,
                    "target_weight_after_control": target_weight,
                }
            )

        return {
            "status": "ok",
            "run_id": allocation.get("run_id"),
            "cycle_id": allocation.get("cycle_id"),
            "mode": allocation.get("mode"),
            "global_guard_decision": allocation.get("global_guard_decision"),
            "target_gross_exposure": round(gross_target, 6),
            "target_net_exposure": round(net_target, 6),
            "items": shaped_items,
            "decision_summary": {
                "symbol_count": len(shaped_items),
                "zero_weight_symbols": sum(
                    1 for item in shaped_items if abs(float(item.get("target_weight_after_control", 0.0) or 0.0)) < 1e-9
                ),
            },
            "as_of": allocation.get("as_of"),
        }

    def allocation_stability_latest(self) -> dict[str, Any]:
        current = self.execution_aware_exposure_shaping_latest()
        current_run_id = current.get("run_id")
        rows = self.repo.store.fetchall_dict(
            """
            SELECT run_id
            FROM execution_quality_snapshots
            ORDER BY created_at DESC
            LIMIT 5
            """
        )
        previous_run_id = None
        for row in rows:
            candidate = str(row.get("run_id") or "")
            if candidate and candidate != current_run_id:
                previous_run_id = candidate
                break

        previous_items_by_symbol: dict[str, dict[str, Any]] = {}
        previous_gross = 0.0
        previous_net = 0.0
        if previous_run_id:
            previous = self.execution_aware_exposure_shaping_by_run(previous_run_id)
            previous_items_by_symbol = {
                str(item.get("symbol") or ""): item for item in list(previous.get("items") or [])
            }
            previous_gross = float(previous.get("target_gross_exposure", 0.0) or 0.0)
            previous_net = float(previous.get("target_net_exposure", 0.0) or 0.0)

        items: list[dict[str, Any]] = []
        changed_count = 0
        for item in list(current.get("items") or []):
            symbol = str(item.get("symbol") or "")
            previous_item = previous_items_by_symbol.get(symbol) or {}
            current_target = float(item.get("target_weight_after_control", 0.0) or 0.0)
            previous_target = float(previous_item.get("target_weight_after_control", 0.0) or 0.0)
            delta = round(current_target - previous_target, 6)
            stability_state = "changed" if abs(delta) >= self.STABILITY_CHANGE_THRESHOLD else "stable"
            if stability_state == "changed":
                changed_count += 1
            items.append(
                {
                    **item,
                    "previous_target_weight": previous_target,
                    "target_weight_delta": delta,
                    "stability_state": stability_state,
                }
            )

        current_gross = float(current.get("target_gross_exposure", 0.0) or 0.0)
        current_net = float(current.get("target_net_exposure", 0.0) or 0.0)
        return {
            "status": "ok",
            "run_id": current_run_id,
            "previous_run_id": previous_run_id,
            "cycle_id": current.get("cycle_id"),
            "mode": current.get("mode"),
            "items": items,
            "gross_delta": round(current_gross - previous_gross, 6),
            "net_delta": round(current_net - previous_net, 6),
            "decision_summary": {
                "symbol_count": len(items),
                "changed_symbols": changed_count,
                "stable_symbols": len(items) - changed_count,
            },
            "as_of": current.get("as_of"),
        }

    def _control_state_penalty(self, item: dict[str, Any]) -> tuple[float, list[str]]:
        reason_codes: list[str] = []
        penalty = 0.0
        global_guard = str(item.get("global_guard_decision") or "continue")
        resolved_control = str(item.get("resolved_control_action") or "allow")
        symbol_control = str(item.get("symbol_control_decision") or "keep")
        allocation_decision = str(item.get("allocation_decision") or "keep")

        if global_guard == "halt":
            penalty = 1.0
            reason_codes.append("global_guard_halt")
        elif global_guard == "pause":
            penalty = max(penalty, 0.8)
            reason_codes.append("global_guard_pause")

        if resolved_control in {"stop", "block", "zero"}:
            penalty = max(penalty, 0.9)
            reason_codes.append(f"resolved_control_{resolved_control}")
        elif resolved_control in {"throttle", "trim"}:
            penalty = max(penalty, 0.6)
            reason_codes.append(f"resolved_control_{resolved_control}")
        elif resolved_control in {"degrade", "pause"}:
            penalty = max(penalty, 0.4)
            reason_codes.append(f"resolved_control_{resolved_control}")

        if symbol_control == "zero":
            penalty = max(penalty, 0.85)
            reason_codes.append("symbol_control_zero")
        elif symbol_control == "trim":
            penalty = max(penalty, 0.5)
            reason_codes.append("symbol_control_trim")

        if allocation_decision == "zero":
            penalty = max(penalty, 1.0)
        elif allocation_decision == "trim":
            penalty = max(penalty, 0.45)

        return penalty, reason_codes

    def _resolve_tradeoff_payload(
        self,
        payload: dict[str, Any],
        *,
        previous_actions_by_symbol: dict[str, dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        previous_actions_by_symbol = previous_actions_by_symbol or {}
        raw_items = list(payload.get("items") or [])
        max_abs_weight = max(
            [abs(float(item.get("current_weight", 0.0) or 0.0)) for item in raw_items] + [1e-9]
        )
        max_abs_drag = max(
            [abs(float(item.get("execution_drag_usd", 0.0) or 0.0)) for item in raw_items] + [1e-9]
        )

        resolved_items: list[dict[str, Any]] = []
        for item in raw_items:
            symbol = str(item.get("symbol") or "")
            current_weight = float(item.get("current_weight", 0.0) or 0.0)
            target_weight = float(item.get("target_weight_after_control", 0.0) or 0.0)
            previous_target_weight = float(item.get("previous_target_weight", 0.0) or 0.0)
            target_weight_delta = float(item.get("target_weight_delta", target_weight - previous_target_weight) or 0.0)
            execution_drag_usd = abs(float(item.get("execution_drag_usd", 0.0) or 0.0))

            conviction_score = self._clamp(abs(current_weight) / max_abs_weight)
            execution_penalty = self._clamp(execution_drag_usd / max_abs_drag)
            concentration_penalty = self._clamp(
                (abs(current_weight) - self.CONCENTRATION_SOFT_LIMIT) / max(1.0 - self.CONCENTRATION_SOFT_LIMIT, 1e-9)
            )
            stability_penalty = self._clamp(abs(target_weight_delta) / max(self.STABILITY_CHANGE_THRESHOLD * 4.0, 1e-9))
            control_penalty, control_reason_codes = self._control_state_penalty(item)

            tradeoff_score = round(
                (0.9 * conviction_score)
                - (0.35 * execution_penalty)
                - (0.25 * concentration_penalty)
                - (0.2 * stability_penalty)
                - (0.4 * control_penalty),
                6,
            )

            resolved_action = "hold"
            resolved_target_weight = round(target_weight, 6)
            tradeoff_reason_codes: list[str] = list(control_reason_codes)

            if abs(target_weight) < 1e-9:
                resolved_action = "zero"
                resolved_target_weight = 0.0
                tradeoff_reason_codes.append("target_weight_zero")
            elif control_penalty >= 0.75 and tradeoff_score < self.TRADEOFF_INCREASE_THRESHOLD:
                resolved_action = "defer"
                resolved_target_weight = round(previous_target_weight, 6)
                tradeoff_reason_codes.append("control_penalty_dominant")
            elif target_weight_delta > self.STABILITY_CHANGE_THRESHOLD and tradeoff_score >= self.TRADEOFF_INCREASE_THRESHOLD:
                resolved_action = "increase"
                tradeoff_reason_codes.append("positive_delta_with_sufficient_score")
            elif (
                target_weight_delta < -self.STABILITY_CHANGE_THRESHOLD
                or str(item.get("allocation_decision") or "keep") == "trim"
                or tradeoff_score < self.TRADEOFF_HOLD_THRESHOLD
            ):
                resolved_action = "trim"
                tradeoff_reason_codes.append("negative_delta_or_penalty_pressure")
            else:
                tradeoff_reason_codes.append("hold_after_tradeoff_balance")

            if concentration_penalty >= 0.5:
                tradeoff_reason_codes.append("concentration_penalty")
            if execution_penalty >= 0.5:
                tradeoff_reason_codes.append("execution_penalty")
            if stability_penalty >= 0.5:
                tradeoff_reason_codes.append("stability_penalty")

            previous_action_row = previous_actions_by_symbol.get(symbol) or {}
            previous_resolved_action = str(previous_action_row.get("resolved_allocation_action") or "none")
            action_changed = previous_resolved_action not in {"", "none"} and previous_resolved_action != resolved_action

            resolved_items.append(
                {
                    **item,
                    "resolved_allocation_action": resolved_action,
                    "resolved_target_weight": resolved_target_weight,
                    "tradeoff_score": tradeoff_score,
                    "tradeoff_breakdown": {
                        "conviction_score": round(conviction_score, 6),
                        "execution_penalty": round(execution_penalty, 6),
                        "concentration_penalty": round(concentration_penalty, 6),
                        "stability_penalty": round(stability_penalty, 6),
                        "control_state_penalty": round(control_penalty, 6),
                    },
                    "tradeoff_reason_codes": tradeoff_reason_codes,
                    "previous_resolved_allocation_action": previous_resolved_action,
                    "action_changed": action_changed,
                }
            )

        return {
            "status": "ok",
            "run_id": payload.get("run_id"),
            "previous_run_id": payload.get("previous_run_id"),
            "cycle_id": payload.get("cycle_id"),
            "mode": payload.get("mode"),
            "items": resolved_items,
            "decision_summary": {
                "symbol_count": len(resolved_items),
                "increase_symbols": sum(1 for item in resolved_items if item.get("resolved_allocation_action") == "increase"),
                "hold_symbols": sum(1 for item in resolved_items if item.get("resolved_allocation_action") == "hold"),
                "trim_symbols": sum(1 for item in resolved_items if item.get("resolved_allocation_action") == "trim"),
                "zero_symbols": sum(1 for item in resolved_items if item.get("resolved_allocation_action") == "zero"),
                "defer_symbols": sum(1 for item in resolved_items if item.get("resolved_allocation_action") == "defer"),
                "changed_actions": sum(1 for item in resolved_items if bool(item.get("action_changed"))),
            },
            "as_of": payload.get("as_of"),
        }

    def allocation_tradeoff_resolution_by_run(self, run_id: str) -> dict[str, Any]:
        payload = self.execution_aware_exposure_shaping_by_run(run_id)
        tradeoff_items: list[dict[str, Any]] = []
        for item in list(payload.get("items") or []):
            tradeoff_items.append(
                {
                    **item,
                    "previous_target_weight": 0.0,
                    "target_weight_delta": float(item.get("target_weight_after_control", 0.0) or 0.0),
                }
            )
        return self._resolve_tradeoff_payload({**payload, "items": tradeoff_items})

    def allocation_tradeoff_resolution_latest(self) -> dict[str, Any]:
        stability = self.allocation_stability_latest()
        previous_run_id = str(stability.get("previous_run_id") or "")
        previous_actions_by_symbol: dict[str, dict[str, Any]] = {}
        if previous_run_id:
            previous_payload = self.allocation_tradeoff_resolution_by_run(previous_run_id)
            previous_actions_by_symbol = {
                str(item.get("symbol") or ""): item for item in list(previous_payload.get("items") or [])
            }
        return self._resolve_tradeoff_payload(stability, previous_actions_by_symbol=previous_actions_by_symbol)

    @staticmethod
    def _intended_objective_for_action(action: str) -> str:
        mapping = {
            "increase": "increase_high_quality_exposure",
            "hold": "preserve_stability",
            "trim": "reduce_drag_or_concentration",
            "zero": "remove_exposure_and_leakage",
            "defer": "avoid_control_dominated_reallocation",
        }
        return mapping.get(str(action or "hold"), "preserve_stability")

    def allocation_outcome_effectiveness_latest(self) -> dict[str, Any]:
        current = self.allocation_tradeoff_resolution_latest()
        previous_run_id = str(current.get("previous_run_id") or "")
        previous_payload = self.allocation_tradeoff_resolution_by_run(previous_run_id) if previous_run_id else {"items": []}
        previous_items_by_symbol = {
            str(item.get("symbol") or ""): item for item in list(previous_payload.get("items") or [])
        }
        current_items_by_symbol = {
            str(item.get("symbol") or ""): item for item in list(current.get("items") or [])
        }

        symbols = sorted(set(previous_items_by_symbol) | set(current_items_by_symbol))
        items: list[dict[str, Any]] = []
        beneficial = 0
        neutral = 0
        adverse = 0

        for symbol in symbols:
            previous_item = previous_items_by_symbol.get(symbol) or {}
            current_item = current_items_by_symbol.get(symbol) or {}

            previous_action = str(previous_item.get("resolved_allocation_action") or "none")
            current_action = str(current_item.get("resolved_allocation_action") or "none")
            previous_drag = float(previous_item.get("execution_drag_usd", 0.0) or 0.0)
            current_drag = float(current_item.get("execution_drag_usd", 0.0) or 0.0)
            previous_weight = float(previous_item.get("resolved_target_weight", previous_item.get("target_weight_after_control", 0.0)) or 0.0)
            current_weight = float(current_item.get("resolved_target_weight", current_item.get("target_weight_after_control", 0.0)) or 0.0)
            previous_notional_share = float(previous_item.get("notional_share", 0.0) or 0.0)
            current_notional_share = float(current_item.get("notional_share", 0.0) or 0.0)
            previous_stability = str(previous_item.get("stability_state") or "unknown")
            current_stability = str(current_item.get("stability_state") or "unknown")

            drag_change = round(current_drag - previous_drag, 6)
            resolved_weight_change = round(current_weight - previous_weight, 6)
            concentration_change = round(current_notional_share - previous_notional_share, 6)
            stability_changed = previous_stability != current_stability and current_stability != "unknown"
            intended_objective = self._intended_objective_for_action(previous_action)

            realized_effect = "neutral"
            realized_reason_codes: list[str] = []
            if previous_action in {"trim", "zero"}:
                if drag_change < -self.OUTCOME_IMPROVEMENT_EPSILON and concentration_change <= self.OUTCOME_IMPROVEMENT_EPSILON:
                    realized_effect = "beneficial"
                    realized_reason_codes.append("drag_reduced_without_concentration_worsening")
                elif concentration_change > self.OUTCOME_IMPROVEMENT_EPSILON:
                    realized_effect = "adverse"
                    realized_reason_codes.append("concentration_worsened")
                elif drag_change > self.OUTCOME_IMPROVEMENT_EPSILON:
                    realized_effect = "adverse"
                    realized_reason_codes.append("drag_increased_after_reduction_action")
                else:
                    realized_reason_codes.append("limited_realized_change")
            elif previous_action == "hold":
                if not stability_changed and abs(resolved_weight_change) < self.STABILITY_CHANGE_THRESHOLD:
                    realized_effect = "beneficial"
                    realized_reason_codes.append("stability_preserved")
                elif stability_changed and abs(resolved_weight_change) >= self.STABILITY_CHANGE_THRESHOLD:
                    realized_effect = "adverse"
                    realized_reason_codes.append("stability_not_preserved")
                else:
                    realized_reason_codes.append("mixed_stability_result")
            elif previous_action == "increase":
                if resolved_weight_change > self.OUTCOME_IMPROVEMENT_EPSILON and drag_change <= self.OUTCOME_IMPROVEMENT_EPSILON:
                    realized_effect = "beneficial"
                    realized_reason_codes.append("higher_exposure_without_drag_worsening")
                elif drag_change > self.OUTCOME_IMPROVEMENT_EPSILON:
                    realized_effect = "adverse"
                    realized_reason_codes.append("drag_worsened_after_increase")
                else:
                    realized_reason_codes.append("increase_not_realized")
            elif previous_action == "defer":
                if abs(resolved_weight_change) < self.STABILITY_CHANGE_THRESHOLD:
                    realized_effect = "beneficial"
                    realized_reason_codes.append("reallocation_successfully_deferred")
                else:
                    realized_effect = "adverse"
                    realized_reason_codes.append("defer_not_respected")
            else:
                realized_reason_codes.append("no_prior_action")

            if realized_effect == "beneficial":
                beneficial += 1
            elif realized_effect == "adverse":
                adverse += 1
            else:
                neutral += 1

            items.append(
                {
                    "symbol": symbol,
                    "evaluated_run_id": current.get("run_id"),
                    "source_run_id": previous_run_id or None,
                    "previous_resolved_allocation_action": previous_action,
                    "current_resolved_allocation_action": current_action,
                    "intended_objective": intended_objective,
                    "previous_execution_drag_usd": previous_drag,
                    "current_execution_drag_usd": current_drag,
                    "drag_change_usd": drag_change,
                    "previous_resolved_target_weight": previous_weight,
                    "current_resolved_target_weight": current_weight,
                    "resolved_weight_change": resolved_weight_change,
                    "previous_notional_share": previous_notional_share,
                    "current_notional_share": current_notional_share,
                    "concentration_change": concentration_change,
                    "previous_stability_state": previous_stability,
                    "current_stability_state": current_stability,
                    "realized_effect": realized_effect,
                    "realized_reason_codes": realized_reason_codes,
                }
            )

        return {
            "status": "ok",
            "run_id": current.get("run_id"),
            "previous_run_id": previous_run_id or None,
            "cycle_id": current.get("cycle_id"),
            "mode": current.get("mode"),
            "items": items,
            "policy_effectiveness_summary": {
                "symbol_count": len(items),
                "beneficial_actions": beneficial,
                "neutral_actions": neutral,
                "adverse_actions": adverse,
                "beneficial_ratio": round(beneficial / len(items), 6) if items else 0.0,
            },
            "as_of": current.get("as_of"),
        }

    def execution_aware_exposure_shaping_by_run(self, run_id: str) -> dict[str, Any]:
        allocation = self._execution_aware_capital_allocation_for_run(run_id)
        items = list(allocation.get("items") or [])
        shaped_items: list[dict[str, Any]] = []
        gross_target = 0.0
        net_target = 0.0

        for item in items:
            current_weight = float(item.get("current_weight", 0.0) or 0.0)
            multiplier = float(item.get("target_capital_multiplier", 0.0) or 0.0)
            target_weight = round(current_weight * multiplier, 6)
            gross_target += abs(target_weight)
            net_target += target_weight
            shaped_items.append({**item, "target_weight_after_control": target_weight})

        return {
            "status": "ok",
            "run_id": allocation.get("run_id"),
            "cycle_id": allocation.get("cycle_id"),
            "mode": allocation.get("mode"),
            "global_guard_decision": allocation.get("global_guard_decision"),
            "target_gross_exposure": round(gross_target, 6),
            "target_net_exposure": round(net_target, 6),
            "items": shaped_items,
            "decision_summary": {
                "symbol_count": len(shaped_items),
                "zero_weight_symbols": sum(
                    1 for item in shaped_items if abs(float(item.get("target_weight_after_control", 0.0) or 0.0)) < 1e-9
                ),
            },
            "as_of": allocation.get("as_of"),
        }
