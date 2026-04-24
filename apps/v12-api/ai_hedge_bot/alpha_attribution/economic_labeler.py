from __future__ import annotations


class EconomicLabeler:
    def label(self, alpha_id: str, exposures: list[dict], residual: dict, regime_rows: list[dict], hidden_flags: list[dict]) -> dict:
        strongest = max(exposures, key=lambda row: float(row.get("exposure_strength", 0.0) or 0.0), default={})
        primary_label = (
            "residual_alpha"
            if str(residual.get("residual_quality") or "").startswith("strong") or str(residual.get("residual_quality") or "").startswith("moderate")
            else f"{strongest.get('factor_name', 'unknown')}_like"
        )
        secondary_labels = []
        if any(bool(row.get("regime_dependency_flag")) for row in regime_rows):
            secondary_labels.append("regime_sensitive")
        if any(bool(row.get("flag")) and alpha_id in {row.get("alpha_id_a"), row.get("alpha_id_b")} for row in hidden_flags):
            secondary_labels.append("hidden_common_driver")
        if str(strongest.get("factor_name") or "") not in {"", "market_beta"}:
            secondary_labels.append("factor_explained")
        recommendation = (
            "scale_allowed"
            if residual.get("residual_alpha_score", 0.0) >= 0.65 and "hidden_common_driver" not in secondary_labels
            else ("requires_monitoring" if residual.get("residual_alpha_score", 0.0) >= 0.50 else "do_not_scale")
        )
        explanation = f"{primary_label} with residual score {residual.get('residual_alpha_score')} and strongest factor {strongest.get('factor_name', 'unknown')}"
        confidence = min(0.95, 0.45 + float(strongest.get("exposure_strength", 0.0) or 0.0))
        return {
            "primary_label": primary_label,
            "secondary_labels": secondary_labels,
            "explanation": explanation,
            "confidence": round(confidence, 6),
            "production_recommendation": recommendation,
        }

