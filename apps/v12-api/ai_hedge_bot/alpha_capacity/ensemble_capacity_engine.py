from __future__ import annotations


class EnsembleCapacityEngine:
    def compute(self, ensemble_id: str, alpha_rows: list[dict]) -> dict:
        if not alpha_rows:
            return {
                "ensemble_id": ensemble_id,
                "total_capacity": 0.0,
                "limiting_alpha": "",
                "scaling_recommendation": "do_not_scale",
            }
        limiting = min(
            alpha_rows,
            key=lambda row: float(row.get("capacity", 0.0) or 0.0) / max(float(row.get("weight", 0.0) or 0.0), 0.01),
        )
        total_capacity = min(
            float(row.get("capacity", 0.0) or 0.0) / max(float(row.get("weight", 0.0) or 0.0), 0.01)
            for row in alpha_rows
        )
        recommendations = {str(row.get("scaling_recommendation") or "") for row in alpha_rows}
        if "do_not_scale" in recommendations:
            scaling = "do_not_scale"
        elif "scale_limited" in recommendations:
            scaling = "scale_limited"
        elif total_capacity >= 0.10:
            scaling = "scale_full"
        else:
            scaling = "scale_partial"
        return {
            "ensemble_id": ensemble_id,
            "total_capacity": round(max(0.0, total_capacity), 6),
            "limiting_alpha": limiting.get("alpha_id"),
            "scaling_recommendation": scaling,
        }

