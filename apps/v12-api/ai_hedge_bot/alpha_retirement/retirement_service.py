from __future__ import annotations

from ai_hedge_bot.alpha_retirement.decision_engine import RetirementDecisionEngine
from ai_hedge_bot.alpha_retirement.health_engine import AlphaHealthEngine
from ai_hedge_bot.alpha_retirement.retirement_input_loader import RetirementInputLoader
from ai_hedge_bot.app.container import CONTAINER
from ai_hedge_bot.core.clock import utc_now_iso
from ai_hedge_bot.core.ids import new_run_id


class AlphaRetirementService:
    def __init__(self) -> None:
        self.store = CONTAINER.runtime_store
        self.loader = RetirementInputLoader()
        self.health = AlphaHealthEngine()
        self.decisions = RetirementDecisionEngine()

    def _latest_run(self) -> dict:
        return self.store.fetchone_dict(
            """
            SELECT *
            FROM alpha_retirement_runs
            ORDER BY completed_at DESC, started_at DESC
            LIMIT 1
            """
        ) or {}

    def _latest_rows(self, table: str, limit: int = 100) -> list[dict]:
        return self.store.fetchall_dict(
            f"""
            SELECT *
            FROM {table}
            ORDER BY created_at DESC
            LIMIT ?
            """,
            [max(int(limit), 1)],
        )

    def _build_latest_payload(self, run: dict, limit: int = 20) -> dict:
        rows = self._latest_rows("alpha_retirement_decisions", limit=max(limit * 3, 30))
        items = [
            {
                "ensemble_id": row.get("ensemble_id"),
                "alpha_id": row.get("alpha_id"),
                "decision": row.get("decision"),
                "kill_switch_action": row.get("kill_switch_action"),
                "decision_reason": row.get("decision_reason"),
                "lifecycle_state": row.get("lifecycle_state"),
            }
            for row in rows[:limit]
        ]
        return {
            "status": "ok",
            "run_id": run.get("run_id"),
            "items": items,
            "alpha_kill_switch_summary": {
                "alpha_count": run.get("alpha_count"),
                "event_count": run.get("event_count"),
                "retirement_count": run.get("retirement_count"),
                "system_alpha_kill_switch_action": "deactivate_or_freeze_deteriorating_alpha_before_portfolio_damage",
            },
            "as_of": run.get("completed_at"),
        }

    def _materialize_run(self, limit: int = 20) -> dict:
        items = self.loader.load(limit=max(limit, 8))
        run_id = new_run_id()
        started_at = utc_now_iso()
        health_rows: list[dict] = []
        event_rows: list[dict] = []
        decision_rows: list[dict] = []
        lifecycle_rows: list[dict] = []
        now = utc_now_iso()

        for item in items:
            health = self.health.score(item)
            decision = self.decisions.decide(item, health)
            lifecycle_state = self._lifecycle_state(decision["decision"])
            health_rows.append(
                {
                    "run_id": run_id,
                    "ensemble_id": item.ensemble_id,
                    "alpha_id": item.alpha_id,
                    "health_score": health["health_score"],
                    "deactivation_pressure": health["deactivation_pressure"],
                    "live_evidence_score": item.live_evidence_score,
                    "crowding_penalty": item.crowding_penalty,
                    "impact_penalty": item.impact_penalty,
                    "weight_delta": item.weight_delta,
                    "health_state": health["health_state"],
                    "created_at": now,
                }
            )
            decision_rows.append(
                {
                    "run_id": run_id,
                    "ensemble_id": item.ensemble_id,
                    "alpha_id": item.alpha_id,
                    "decision": decision["decision"],
                    "kill_switch_action": decision["kill_switch_action"],
                    "decision_reason": decision["decision_reason"],
                    "lifecycle_state": lifecycle_state,
                    "mpi_notification": self._mpi_notification(decision["kill_switch_action"]),
                    "lcc_notification": self._lcc_notification(decision["kill_switch_action"]),
                    "created_at": now,
                }
            )
            if decision["kill_switch_action"] != "continue":
                event_rows.append(
                    {
                        "run_id": run_id,
                        "ensemble_id": item.ensemble_id,
                        "alpha_id": item.alpha_id,
                        "event_type": decision["kill_switch_action"],
                        "severity": self._severity(decision["kill_switch_action"]),
                        "event_reason": decision["decision_reason"],
                        "created_at": now,
                    }
                )
            lifecycle_rows.append(
                {
                    "run_id": run_id,
                    "alpha_id": item.alpha_id,
                    "previous_state": "active",
                    "next_state": lifecycle_state,
                    "aae_update_payload": f"alpha_id={item.alpha_id};state={lifecycle_state};reason={decision['decision_reason']}",
                    "created_at": now,
                }
            )

        self.store.append(
            "alpha_retirement_runs",
            {
                "run_id": run_id,
                "started_at": started_at,
                "completed_at": utc_now_iso(),
                "alpha_count": len(decision_rows),
                "event_count": len(event_rows),
                "retirement_count": sum(1 for row in decision_rows if row["decision"] == "retire_alpha"),
                "status": "ok",
                "notes": "aes07_alpha_kill_switch_retirement",
            },
        )
        if health_rows:
            self.store.append("alpha_live_health", health_rows)
        if event_rows:
            self.store.append("alpha_kill_switch_events", event_rows)
        if decision_rows:
            self.store.append("alpha_retirement_decisions", decision_rows)
        if lifecycle_rows:
            self.store.append("alpha_lifecycle_updates", lifecycle_rows)
        return self._build_latest_payload(self._latest_run(), limit=limit)

    def _lifecycle_state(self, decision: str) -> str:
        return {
            "retire_alpha": "retired",
            "freeze_alpha": "frozen",
            "reduce_alpha": "active_reduced",
            "continue_alpha": "active",
        }.get(decision, "active")

    def _severity(self, action: str) -> str:
        return {"deactivate": "critical", "freeze": "high", "reduce": "medium"}.get(action, "low")

    def _mpi_notification(self, action: str) -> str:
        return f"mpi_alpha_weight_action={action}"

    def _lcc_notification(self, action: str) -> str:
        return f"lcc_runtime_control_action={action}"

    def run(self, limit: int = 20) -> dict:
        latest_run = self._latest_run()
        if latest_run:
            latest = self.latest(limit=limit)
            if list(latest.get("items") or []):
                return latest
        return self._materialize_run(limit=limit)

    def latest(self, limit: int = 20) -> dict:
        run = self._latest_run()
        if not run:
            return self.run(limit=limit)
        rows = self._latest_rows("alpha_retirement_decisions", limit=max(limit * 3, 30))
        if not rows:
            return self._materialize_run(limit=limit)
        return self._build_latest_payload(run, limit=limit)

    def alpha_kill_switch_alpha(self, alpha_id: str) -> dict:
        self.latest(limit=20)
        health = self.store.fetchone_dict(
            """
            SELECT *
            FROM alpha_live_health
            WHERE alpha_id=?
            ORDER BY created_at DESC
            LIMIT 1
            """,
            [alpha_id],
        ) or {}
        decision = self.store.fetchone_dict(
            """
            SELECT *
            FROM alpha_retirement_decisions
            WHERE alpha_id=?
            ORDER BY created_at DESC
            LIMIT 1
            """,
            [alpha_id],
        ) or {}
        events = self.store.fetchall_dict(
            """
            SELECT *
            FROM alpha_kill_switch_events
            WHERE alpha_id=?
            ORDER BY created_at DESC
            LIMIT 20
            """,
            [alpha_id],
        )
        return {"status": "ok" if decision else "not_found", "alpha_id": alpha_id, "health": health, "decision": decision, "events": events}

    def alpha_retirement_latest(self, limit: int = 20) -> dict:
        self.latest(limit=limit)
        rows = self._latest_rows("alpha_retirement_decisions", limit=max(limit * 3, 30))
        return {"status": "ok", "items": rows[:limit], "alpha_retirement_summary": {"retirement_count": sum(1 for row in rows[:limit] if row.get("decision") == "retire_alpha")}}

    def alpha_retirement_alpha(self, alpha_id: str) -> dict:
        payload = self.alpha_kill_switch_alpha(alpha_id)
        lifecycle = self.store.fetchone_dict(
            """
            SELECT *
            FROM alpha_lifecycle_updates
            WHERE alpha_id=?
            ORDER BY created_at DESC
            LIMIT 1
            """,
            [alpha_id],
        ) or {}
        payload["lifecycle_update"] = lifecycle
        return payload

    def alpha_deactivation_decisions_latest(self, limit: int = 20) -> dict:
        self.latest(limit=limit)
        rows = self._latest_rows("alpha_retirement_decisions", limit=max(limit * 3, 30))
        items = [row for row in rows if row.get("kill_switch_action") != "continue"][:limit]
        return {"status": "ok", "items": items, "alpha_deactivation_summary": {"deactivation_count": len(items)}}

    def alpha_kill_switch_events_latest(self, limit: int = 20) -> dict:
        self.latest(limit=limit)
        rows = self._latest_rows("alpha_kill_switch_events", limit=max(limit * 3, 30))
        return {"status": "ok", "items": rows[:limit], "alpha_kill_switch_event_summary": {"event_count": len(rows[:limit])}}

    def override(self, alpha_id: str = "manual.override", action: str = "continue", reason: str = "operator_override") -> dict:
        row = {
            "override_id": new_run_id(),
            "alpha_id": alpha_id,
            "override_action": action,
            "override_reason": reason,
            "created_at": utc_now_iso(),
        }
        self.store.append("alpha_kill_switch_overrides", row)
        return {"status": "ok", "override": row}

