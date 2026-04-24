from __future__ import annotations

from collections import defaultdict

from ai_hedge_bot.alpha_weighting.constraint_engine import ConstraintEngine
from ai_hedge_bot.alpha_weighting.live_state_model import LiveStateModel
from ai_hedge_bot.alpha_weighting.proposal_engine import ProposalEngine
from ai_hedge_bot.alpha_weighting.smoothing_engine import SmoothingEngine
from ai_hedge_bot.alpha_weighting.target_weight_engine import TargetWeightEngine
from ai_hedge_bot.alpha_weighting.weighting_input_loader import WeightingInputLoader
from ai_hedge_bot.app.container import CONTAINER
from ai_hedge_bot.core.clock import utc_now_iso
from ai_hedge_bot.core.ids import new_run_id


class AlphaWeightingService:
    def __init__(self) -> None:
        self.store = CONTAINER.runtime_store
        self.loader = WeightingInputLoader()
        self.live_state = LiveStateModel()
        self.target = TargetWeightEngine()
        self.smoothing = SmoothingEngine()
        self.constraints = ConstraintEngine()
        self.proposal = ProposalEngine()

    def _latest_run(self) -> dict:
        return self.store.fetchone_dict(
            """
            SELECT *
            FROM alpha_weighting_runs
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
        rows = self._latest_rows("alpha_dynamic_weights", limit=max(limit * 3, 30))
        items = [
            {
                "ensemble_id": row.get("ensemble_id"),
                "alpha_id": row.get("alpha_id"),
                "current_weight": row.get("current_weight"),
                "target_weight": row.get("target_weight"),
                "smoothed_weight": row.get("smoothed_weight"),
                "final_weight": row.get("final_weight"),
                "weight_change_reason": row.get("weight_change_reason"),
            }
            for row in rows[:limit]
        ]
        return {
            "status": "ok",
            "run_id": run.get("run_id"),
            "items": items,
            "alpha_dynamic_weight_summary": {
                "alpha_count": run.get("alpha_count"),
                "ensemble_count": run.get("ensemble_count"),
                "proposal_count": run.get("proposal_count"),
                "system_alpha_weighting_action": "send_constrained_dynamic_weights_to_mpi_and_lcc",
            },
            "as_of": run.get("completed_at"),
        }

    def _materialize_run(self, limit: int = 20) -> dict:
        items = self.loader.load(limit=max(limit, 8))
        run_id = new_run_id()
        started_at = utc_now_iso()
        states = {item.alpha_id: self.live_state.score(item) for item in items}
        targets = self.target.compute(items, states)
        smoothed = {item.alpha_id: self.smoothing.smooth(item, targets[item.alpha_id]) for item in items}
        finals, constraints = self.constraints.apply(items, smoothed)

        state_rows: list[dict] = []
        signal_rows: list[dict] = []
        weight_rows: list[dict] = []
        constraint_rows: list[dict] = []
        now = utc_now_iso()
        for item in items:
            state = states[item.alpha_id]
            constraint = constraints[item.alpha_id]
            final_weight = finals[item.alpha_id]
            reason = self._reason(item, state, final_weight)
            state_rows.append(
                {
                    "run_id": run_id,
                    "ensemble_id": item.ensemble_id,
                    "alpha_id": item.alpha_id,
                    "return_signal": state["return_signal"],
                    "capacity_signal": state["capacity_signal"],
                    "liquidity_signal": state["liquidity_signal"],
                    "crowding_penalty": state["crowding_penalty"],
                    "impact_penalty": state["impact_penalty"],
                    "live_evidence_score": state["live_evidence_score"],
                    "created_at": now,
                }
            )
            signal_rows.append(
                {
                    "run_id": run_id,
                    "ensemble_id": item.ensemble_id,
                    "alpha_id": item.alpha_id,
                    "signal_name": reason,
                    "signal_value": state["live_evidence_score"],
                    "created_at": now,
                }
            )
            weight_rows.append(
                {
                    "run_id": run_id,
                    "ensemble_id": item.ensemble_id,
                    "alpha_id": item.alpha_id,
                    "current_weight": item.current_weight,
                    "target_weight": targets[item.alpha_id],
                    "smoothed_weight": smoothed[item.alpha_id],
                    "final_weight": final_weight,
                    "weight_delta": round(final_weight - item.current_weight, 6),
                    "weight_change_reason": reason,
                    "constraint_action": constraint["constraint_action"],
                    "created_at": now,
                }
            )
            constraint_rows.append(
                {
                    "run_id": run_id,
                    "ensemble_id": item.ensemble_id,
                    "alpha_id": item.alpha_id,
                    "max_weight": constraint["max_weight"],
                    "max_delta": constraint["max_delta"],
                    "lower_bound": constraint["lower_bound"],
                    "upper_bound": constraint["upper_bound"],
                    "constraint_action": constraint["constraint_action"],
                    "created_at": now,
                }
            )

        proposal_rows = []
        for ensemble_id, rows in self._group_by_ensemble(weight_rows).items():
            proposal = self.proposal.build(ensemble_id, rows)
            proposal_rows.append({**proposal, "run_id": run_id, "created_at": utc_now_iso()})

        self.store.append(
            "alpha_weighting_runs",
            {
                "run_id": run_id,
                "started_at": started_at,
                "completed_at": utc_now_iso(),
                "alpha_count": len(weight_rows),
                "ensemble_count": len(proposal_rows),
                "proposal_count": len(proposal_rows),
                "status": "ok",
                "notes": "aes06_dynamic_alpha_weighting",
            },
        )
        if state_rows:
            self.store.append("alpha_live_state", state_rows)
        if signal_rows:
            self.store.append("alpha_weight_signals", signal_rows)
        if weight_rows:
            self.store.append("alpha_dynamic_weights", weight_rows)
        if constraint_rows:
            self.store.append("alpha_weight_constraints", constraint_rows)
        if proposal_rows:
            self.store.append("alpha_weight_proposals", proposal_rows)
        return self._build_latest_payload(self._latest_run(), limit=limit)

    def _group_by_ensemble(self, rows: list[dict]) -> dict[str, list[dict]]:
        grouped: dict[str, list[dict]] = defaultdict(list)
        for row in rows:
            grouped[str(row.get("ensemble_id") or "ensemble.1")].append(row)
        return grouped

    def _reason(self, item, state: dict, final_weight: float) -> str:
        if item.scaling_recommendation == "do_not_scale":
            return "capacity_block"
        if state["crowding_penalty"] > 0.75:
            return "crowding_penalty"
        if final_weight > item.current_weight:
            return "positive_live_evidence"
        if final_weight < item.current_weight:
            return "risk_or_capacity_reduction"
        return "hold_weight"

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
        rows = self._latest_rows("alpha_dynamic_weights", limit=max(limit * 3, 30))
        if not rows:
            return self._materialize_run(limit=limit)
        return self._build_latest_payload(run, limit=limit)

    def alpha_dynamic_weights_ensemble(self, ensemble_id: str) -> dict:
        self.latest(limit=20)
        rows = self.store.fetchall_dict(
            """
            SELECT *
            FROM alpha_dynamic_weights
            WHERE ensemble_id=?
            ORDER BY final_weight DESC, alpha_id ASC
            LIMIT 50
            """,
            [ensemble_id],
        )
        proposal = self.store.fetchone_dict(
            """
            SELECT *
            FROM alpha_weight_proposals
            WHERE ensemble_id=?
            ORDER BY created_at DESC
            LIMIT 1
            """,
            [ensemble_id],
        ) or {}
        return {"status": "ok" if rows else "not_found", "ensemble_id": ensemble_id, "weights": rows, "proposal": proposal}

    def alpha_weight_adjustments_latest(self, limit: int = 20) -> dict:
        self.latest(limit=limit)
        rows = self._latest_rows("alpha_dynamic_weights", limit=max(limit * 3, 30))
        return {"status": "ok", "items": rows[:limit], "alpha_weight_adjustment_summary": {"adjustment_count": len(rows[:limit])}}

    def alpha_weight_drift_latest(self, limit: int = 20) -> dict:
        self.latest(limit=limit)
        rows = self._latest_rows("alpha_dynamic_weights", limit=max(limit * 3, 30))
        items = [
            {
                "ensemble_id": row.get("ensemble_id"),
                "alpha_id": row.get("alpha_id"),
                "weight_delta": row.get("weight_delta"),
                "drift_flag": abs(float(row.get("weight_delta") or 0.0)) > 0.04,
            }
            for row in rows[:limit]
        ]
        return {"status": "ok", "items": items, "alpha_weight_drift_summary": {"drift_count": sum(1 for item in items if item["drift_flag"])}}

    def alpha_weight_constraints_latest(self, limit: int = 20) -> dict:
        self.latest(limit=limit)
        rows = self._latest_rows("alpha_weight_constraints", limit=max(limit * 3, 30))
        return {"status": "ok", "items": rows[:limit], "alpha_weight_constraint_summary": {"constraint_count": len(rows[:limit])}}

    def alpha_weight_proposals_latest(self, limit: int = 20) -> dict:
        self.latest(limit=limit)
        rows = self._latest_rows("alpha_weight_proposals", limit=max(limit * 3, 30))
        return {"status": "ok", "items": rows[:limit], "alpha_weight_proposal_summary": {"proposal_count": len(rows[:limit])}}

