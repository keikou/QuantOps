from __future__ import annotations


class AttributionDecisionEngine:
    def decide(self, residual: dict, concentration_rows: list[dict], label: dict, hidden_flags: list[dict], alpha_id: str) -> dict:
        concentration_breach = any(bool(row.get("concentration_flag")) for row in concentration_rows)
        hidden_flag = any(bool(row.get("flag")) and alpha_id in {row.get("alpha_id_a"), row.get("alpha_id_b")} for row in hidden_flags)
        recommendation = str(label.get("production_recommendation") or "requires_monitoring")
        if concentration_breach or hidden_flag:
            recommendation = "do_not_scale"
        elif residual.get("residual_alpha_score", 0.0) >= 0.60 and not concentration_breach:
            recommendation = "scale_allowed"
        elif residual.get("residual_alpha_score", 0.0) >= 0.48:
            recommendation = "scale_limited"
        return {
            "production_recommendation": recommendation,
            "economic_risk_state": "elevated" if concentration_breach or hidden_flag else ("moderate" if recommendation == "scale_limited" else "contained"),
        }

