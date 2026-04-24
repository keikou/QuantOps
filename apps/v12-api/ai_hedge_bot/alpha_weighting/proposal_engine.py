from __future__ import annotations


class ProposalEngine:
    def build(self, ensemble_id: str, rows: list[dict]) -> dict:
        max_abs_change = max((abs(float(row["final_weight"]) - float(row["current_weight"])) for row in rows), default=0.0)
        capped_count = sum(1 for row in rows if row.get("constraint_action") != "accepted")
        proposal_status = "lcc_review_required" if capped_count or max_abs_change > 0.04 else "mpi_ready"
        return {
            "ensemble_id": ensemble_id,
            "proposal_status": proposal_status,
            "max_abs_weight_change": round(max_abs_change, 6),
            "constraint_event_count": capped_count,
            "mpi_intent": "use_constrained_dynamic_alpha_weights",
            "lcc_review_reason": "constraint_events_or_large_weight_change" if proposal_status != "mpi_ready" else "none",
        }

