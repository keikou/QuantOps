from __future__ import annotations

from typing import Any

from ai_hedge_bot.app.container import CONTAINER
from ai_hedge_bot.core.clock import utc_now_iso
from ai_hedge_bot.core.ids import new_cycle_id
from ai_hedge_bot.research_factory.governance_state import GovernanceStateBridge


class SelfImprovingService:
    def __init__(self) -> None:
        self.store = CONTAINER.runtime_store
        self.bridge = GovernanceStateBridge()

    def evaluate_result_evidence(self, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        payload = payload or {}
        created_at = str(payload.get("created_at") or utc_now_iso())
        model_id = str(payload.get("model_id") or "model_seed")
        strategy_id = str(payload.get("strategy_id") or "trend_core")
        expected_return = float(payload.get("expected_return", 0.0))
        realized_return = float(payload.get("realized_return", 0.0))
        hit_rate = float(payload.get("hit_rate", 0.0))
        turnover = float(payload.get("turnover", 0.0))
        drawdown = abs(float(payload.get("drawdown", 0.0)))
        slippage = float(payload.get("slippage_bps", 0.0))
        fill_rate = float(payload.get("fill_rate", 0.0))
        risk_usage = float(payload.get("risk_usage", 0.0))

        thresholds = {
            "pnl_drift_alert": float(payload.get("pnl_drift_alert", 0.08)),
            "slippage_alert_bps": float(payload.get("slippage_alert_bps", 12.0)),
            "fill_rate_floor": float(payload.get("fill_rate_floor", 0.82)),
            "drawdown_alert": float(payload.get("drawdown_alert", 0.12)),
        }

        pnl_drift = max(0.0, expected_return - realized_return)
        flags: list[str] = []
        if pnl_drift > thresholds["pnl_drift_alert"]:
            flags.append("pnl_drift")
        if slippage > thresholds["slippage_alert_bps"]:
            flags.append("slippage_drift")
        if fill_rate < thresholds["fill_rate_floor"]:
            flags.append("fill_rate_weak")
        if drawdown > thresholds["drawdown_alert"]:
            flags.append("drawdown_breach")
        if hit_rate < 0.5:
            flags.append("hit_rate_weak")

        decision = "keep"
        if {"drawdown_breach", "slippage_drift"} & set(flags):
            decision = "rollback"
        elif {"pnl_drift", "fill_rate_weak"} & set(flags):
            decision = "reduce_capital"
        elif "hit_rate_weak" in flags:
            decision = "shadow"

        record = {
            "review_id": f"self_improve_{new_cycle_id()}",
            "created_at": created_at,
            "model_id": model_id,
            "strategy_id": strategy_id,
            "decision": decision,
            "pnl_drift": pnl_drift,
            "hit_rate": hit_rate,
            "slippage_bps": slippage,
            "fill_rate": fill_rate,
            "turnover": turnover,
            "risk_usage": risk_usage,
            "flags_json": self.store.to_json(flags),
            "notes": str(payload.get("notes") or "phase7 self improving evaluation"),
        }
        self.store.append("model_live_reviews", record)

        model_target, alpha_target = self._governance_targets(decision)
        if model_target:
            self.bridge.transition_model(model_id, model_target, f"self_improving_{decision}", created_at)
        alpha_id = self.bridge.alpha_id_for_model(model_id)
        if alpha_id and alpha_target:
            self.bridge.transition_alpha(alpha_id, alpha_target, "self_improving", f"self_improving_{decision}", created_at)
            self._persist_runtime_deploy_state(
                alpha_id=alpha_id,
                decision=decision,
                created_at=created_at,
                pnl_drift=pnl_drift,
                hit_rate=hit_rate,
                slippage_bps=slippage,
            )

        return {
            "status": "ok",
            "model_id": model_id,
            "strategy_id": strategy_id,
            "decision": decision,
            "flags": flags,
            "pnl_drift": pnl_drift,
            "hit_rate": hit_rate,
            "slippage_bps": slippage,
            "fill_rate": fill_rate,
            "turnover": turnover,
            "risk_usage": risk_usage,
        }

    def _persist_runtime_deploy_state(
        self,
        *,
        alpha_id: str,
        decision: str,
        created_at: str,
        pnl_drift: float,
        hit_rate: float,
        slippage_bps: float,
    ) -> None:
        if decision == "keep":
            rank_score = max(0.0, min(1.0, 0.82 + hit_rate * 0.1 - min(slippage_bps, 20.0) / 400.0))
            self.store.append(
                "alpha_rankings",
                {
                    "ranking_id": new_cycle_id(),
                    "created_at": created_at,
                    "alpha_id": alpha_id,
                    "rank_score": rank_score,
                    "expected_return": max(0.0, 0.12 - pnl_drift),
                    "risk_adjusted_score": rank_score,
                    "execution_cost_adjusted_score": max(0.0, rank_score - slippage_bps / 200.0),
                    "diversification_value": 0.4,
                    "recommended_action": "promote",
                },
            )
            self.store.append(
                "alpha_promotions",
                {
                    "promotion_id": new_cycle_id(),
                    "created_at": created_at,
                    "alpha_id": alpha_id,
                    "decision": "promote",
                    "source_run_id": f"self_improving_{decision}",
                    "notes": "phase7 self improving deploy",
                },
            )
        elif decision == "rollback":
            self.store.append(
                "alpha_demotions",
                {
                    "demotion_id": new_cycle_id(),
                    "created_at": created_at,
                    "alpha_id": alpha_id,
                    "decision": "rollback",
                    "source_run_id": f"self_improving_{decision}",
                    "notes": "phase7 self improving rollback",
                },
            )

    def _governance_targets(self, decision: str) -> tuple[str | None, str | None]:
        if decision == "keep":
            return "live", "promoted"
        if decision == "reduce_capital":
            return "approved", "monitor"
        if decision == "shadow":
            return "shadow", "shadow"
        if decision == "rollback":
            return "rolled_back", "retired"
        return None, None
