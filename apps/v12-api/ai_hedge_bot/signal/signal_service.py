from __future__ import annotations

import math
from datetime import datetime, timezone

from ai_hedge_bot.app.container import CONTAINER
from ai_hedge_bot.core.enums import Side, Regime
from ai_hedge_bot.core.ids import new_signal_id
from ai_hedge_bot.core.phaseg_types import SignalCandidate
from ai_hedge_bot.core.clock import utc_now_iso


class SignalService:
    def _latest_runtime_alpha_overlay(self, symbols: list[str]) -> dict | None:
        row = CONTAINER.runtime_store.fetchone_dict(
            """
            SELECT
                p.alpha_id,
                p.source_run_id,
                reg.alpha_family,
                reg.factor_type,
                lib.state AS governance_state,
                COALESCE(r.rank_score, 0.0) AS rank_score,
                COALESCE(r.recommended_action, p.decision) AS recommended_action,
                mr.model_id
            FROM alpha_promotions p
            LEFT JOIN (
                SELECT alpha_id, alpha_family, factor_type
                FROM (
                    SELECT
                        alpha_id,
                        alpha_family,
                        factor_type,
                        created_at,
                        ROW_NUMBER() OVER (PARTITION BY alpha_id ORDER BY created_at DESC) AS rn
                    FROM alpha_registry
                ) t
                WHERE rn = 1
            ) reg
                ON reg.alpha_id = p.alpha_id
            LEFT JOIN (
                SELECT alpha_id, state
                FROM (
                    SELECT
                        alpha_id,
                        state,
                        created_at,
                        ROW_NUMBER() OVER (PARTITION BY alpha_id ORDER BY created_at DESC) AS rn
                    FROM alpha_library
                ) t
                WHERE rn = 1
            ) lib
                ON lib.alpha_id = p.alpha_id
            LEFT JOIN (
                SELECT alpha_id, rank_score, recommended_action
                FROM (
                    SELECT
                        alpha_id,
                        rank_score,
                        recommended_action,
                        created_at,
                        ROW_NUMBER() OVER (PARTITION BY alpha_id ORDER BY created_at DESC) AS rn
                    FROM alpha_rankings
                ) t
                WHERE rn = 1
            ) r
                ON r.alpha_id = p.alpha_id
            LEFT JOIN (
                SELECT experiment_id, model_id
                FROM (
                    SELECT
                        experiment_id,
                        model_id,
                        created_at,
                        ROW_NUMBER() OVER (PARTITION BY experiment_id ORDER BY created_at DESC) AS rn
                    FROM model_registry
                ) t
                WHERE rn = 1
            ) mr
                ON mr.experiment_id = (
                    SELECT experiment_id
                    FROM experiment_tracker e
                    WHERE e.alpha_id = p.alpha_id
                    ORDER BY e.created_at DESC
                    LIMIT 1
                )
            WHERE lower(coalesce(p.decision, '')) = 'promote'
            ORDER BY p.created_at DESC
            LIMIT 1
            """
        )
        if not row or not symbols:
            return None

        governance_state = str(row.get("governance_state") or "").lower()
        if governance_state and governance_state not in {"promoted", "approved", "live", "monitor"}:
            return None

        alpha_id = str(row.get("alpha_id") or "")
        family = str(row.get("alpha_family") or "").lower()
        factor_type = str(row.get("factor_type") or "").lower()
        selector = f"{family}:{factor_type}:{alpha_id}"

        preferred_symbol = symbols[0]
        if "carry" in selector or "breakout" in selector or "trend" in selector:
            preferred_symbol = "BTCUSDT" if "BTCUSDT" in symbols else symbols[0]
        elif "momentum" in selector:
            preferred_symbol = "ETHUSDT" if "ETHUSDT" in symbols else symbols[0]
        elif "reversion" in selector or "mean" in selector:
            preferred_symbol = "SOLUSDT" if "SOLUSDT" in symbols else symbols[0]
        elif "flow" in selector or "liquid" in selector:
            preferred_symbol = "DOGEUSDT" if "DOGEUSDT" in symbols else symbols[0]

        boost = min(0.24, 0.08 + float(row.get("rank_score", 0.0) or 0.0) * 0.12)
        return {
            "alpha_id": alpha_id,
            "model_id": str(row.get("model_id") or ""),
            "decision_source": str(row.get("source_run_id") or ""),
            "preferred_symbol": preferred_symbol,
            "boost": boost,
            "recommended_action": str(row.get("recommended_action") or "promote"),
            "governance_state": governance_state or "promoted",
        }

    def generate(self, symbols: list[str]) -> list[dict]:
        now = datetime.now(timezone.utc)
        minute_bucket = now.hour * 60 + now.minute
        drift = math.sin(minute_bucket / 11.0)
        overlay = self._latest_runtime_alpha_overlay(symbols)

        results = []
        for idx, symbol in enumerate(symbols):
            phase = minute_bucket / (5.0 + idx)
            raw_score = (
                0.58
                + 0.18 * math.sin(phase)
                + 0.08 * math.cos(phase / 2.0 + idx)
                + 0.03 * drift
            )
            dominant_alpha = "phase6_dynamic_alpha"
            metadata = {
                "source": "phase6_dynamic_signal",
                "generated_at": utc_now_iso(),
                "minute_bucket": minute_bucket,
                "drift": round(drift, 6),
            }
            if overlay and symbol == overlay["preferred_symbol"]:
                raw_score += float(overlay["boost"])
                dominant_alpha = str(overlay["alpha_id"] or dominant_alpha)
                metadata["runtime_alpha_linked"] = True
                metadata["runtime_alpha_action"] = overlay["recommended_action"]
                metadata["runtime_alpha_boost"] = round(float(overlay["boost"]), 6)
                metadata["runtime_alpha_id"] = str(overlay["alpha_id"] or "")
                metadata["runtime_model_id"] = str(overlay.get("model_id") or "")
                metadata["runtime_decision_source"] = str(overlay.get("decision_source") or "")
                metadata["runtime_governance_state"] = str(overlay.get("governance_state") or "")
            elif overlay:
                metadata["runtime_alpha_linked"] = False
                metadata["selected_runtime_alpha"] = str(overlay["alpha_id"] or "")
                metadata["selected_runtime_model_id"] = str(overlay.get("model_id") or "")
                metadata["selected_runtime_decision_source"] = str(overlay.get("decision_source") or "")
            score = round(max(0.05, min(0.95, raw_score)), 4)
            side = Side.LONG if math.sin(phase + idx) >= 0 else Side.SHORT

            if abs(drift) < 0.25:
                regime = Regime.NEUTRAL
            elif abs(drift) > 0.85:
                regime = Regime.VOLATILE
            else:
                regime = Regime.TREND if drift > 0 else Regime.MEAN_REVERSION

            sig = SignalCandidate(
                signal_id=new_signal_id(),
                symbol=symbol,
                side=side,
                score=score,
                dominant_alpha=dominant_alpha,
                alpha_family="cross_sectional",
                horizon="intraday",
                turnover_profile="medium",
                regime=regime,
                metadata=metadata,
            )
            results.append(sig.to_dict())

        return results
