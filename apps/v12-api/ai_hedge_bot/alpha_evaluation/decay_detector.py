from __future__ import annotations


class DecayDetector:
    def analyze(self, rows: list[dict]) -> dict:
        values = [float(row.get("cost_adjusted_return", 0.0) or 0.0) for row in rows]
        if not values:
            return {"decay_score": 0.0, "decay_status": "unknown", "early_mean": 0.0, "recent_mean": 0.0}
        mid = max(len(values) // 2, 1)
        early = values[:mid]
        recent = values[mid:] or values[-1:]
        early_mean = sum(early) / len(early)
        recent_mean = sum(recent) / len(recent)
        if early_mean <= 0:
            decay_score = 0.5
        else:
            decay_score = max(0.0, min(recent_mean / (early_mean + 1e-9), 1.0))
        status = "stable"
        if decay_score < 0.55:
            status = "severe"
        elif decay_score < 0.8:
            status = "moderate"
        return {
            "decay_score": round(decay_score, 6),
            "decay_status": status,
            "early_mean": round(early_mean, 6),
            "recent_mean": round(recent_mean, 6),
        }

