from __future__ import annotations

from typing import Any

from ai_hedge_bot.app.container import CONTAINER
from ai_hedge_bot.core.clock import utc_now_iso
from ai_hedge_bot.core.ids import new_cycle_id
from ai_hedge_bot.research_factory.service import ResearchFactoryService
from ai_hedge_bot.services.alpha_strategy_selection_intelligence_service import (
    AlphaStrategySelectionIntelligenceService,
)


class ResearchPromotionIntelligenceService:
    RETIRE_THRESHOLD = 0.32

    def __init__(self) -> None:
        self.selection = AlphaStrategySelectionIntelligenceService()
        self.research = ResearchFactoryService()
        self.store = CONTAINER.runtime_store

    def promotion_agenda_latest(self, limit: int = 20) -> dict[str, Any]:
        slate = self.selection.effective_selection_slate_latest(limit=limit)
        items: list[dict[str, Any]] = []

        for item in list(slate.get("items") or []):
            state = str(item.get("state") or "candidate")
            effective_status = str(item.get("effective_status") or "returned_to_research")
            selection_score = float(item.get("selection_score", 0.0) or 0.0)

            promotion_action = "stay_queued"
            rationale = "await_more_evidence"

            if effective_status == "selected_for_promotion_review":
                promotion_action = "promote"
                rationale = "promotion_review_selected"
            elif effective_status == "selected_for_shadow_review":
                promotion_action = "advance"
                rationale = "shadow_review_selected"
            elif effective_status == "returned_to_research" and state == "promoted":
                promotion_action = "demote"
                rationale = "promoted_alpha_returned_to_research"
            elif effective_status == "deferred" and selection_score < self.RETIRE_THRESHOLD:
                promotion_action = "retire"
                rationale = "low_quality_deferred_candidate"
            elif effective_status == "returned_to_research":
                promotion_action = "stay_queued"
                rationale = "research_return_requires_more_work"
            elif effective_status == "deferred":
                promotion_action = "stay_queued"
                rationale = "deferred_but_not_retired"

            review_priority = "normal"
            if promotion_action == "promote":
                review_priority = "immediate"
            elif promotion_action in {"advance", "demote"}:
                review_priority = "high"
            elif promotion_action == "retire":
                review_priority = "low"

            items.append(
                {
                    **item,
                    "promotion_action": promotion_action,
                    "promotion_rationale": rationale,
                    "review_priority": review_priority,
                }
            )

        return {
            "status": "ok",
            "run_id": slate.get("run_id"),
            "cycle_id": slate.get("cycle_id"),
            "mode": slate.get("mode"),
            "items": items,
            "decision_summary": {
                "alpha_count": len(items),
                "promote_actions": sum(1 for item in items if item.get("promotion_action") == "promote"),
                "advance_actions": sum(1 for item in items if item.get("promotion_action") == "advance"),
                "stay_queued_actions": sum(1 for item in items if item.get("promotion_action") == "stay_queued"),
                "demote_actions": sum(1 for item in items if item.get("promotion_action") == "demote"),
                "retire_actions": sum(1 for item in items if item.get("promotion_action") == "retire"),
            },
            "control_context": slate.get("control_context"),
            "as_of": slate.get("as_of"),
        }

    def promotion_candidate_docket_latest(self, limit: int = 20) -> dict[str, Any]:
        agenda = self.promotion_agenda_latest(limit=limit)
        experiments = self.research.experiments.list_latest(limit=200)
        models = self.research.models.list_latest(limit=200)
        latest_experiment_by_alpha: dict[str, dict[str, Any]] = {}
        for experiment in experiments:
            alpha_id = str(experiment.get("alpha_id") or "")
            if alpha_id and alpha_id not in latest_experiment_by_alpha:
                latest_experiment_by_alpha[alpha_id] = experiment

        latest_model_by_experiment: dict[str, dict[str, Any]] = {}
        for model in models:
            experiment_id = str(model.get("experiment_id") or "")
            if experiment_id and experiment_id not in latest_model_by_experiment:
                latest_model_by_experiment[experiment_id] = model

        items: list[dict[str, Any]] = []
        for item in list(agenda.get("items") or []):
            alpha_id = str(item.get("alpha_id") or "")
            experiment = latest_experiment_by_alpha.get(alpha_id) or {}
            model = latest_model_by_experiment.get(str(experiment.get("experiment_id") or "")) or {}
            docket_status = "queued_for_review"
            if str(item.get("promotion_action") or "") == "promote":
                docket_status = "promotion_candidate"
            elif str(item.get("promotion_action") or "") == "advance":
                docket_status = "shadow_candidate"
            elif str(item.get("promotion_action") or "") == "demote":
                docket_status = "demotion_candidate"
            elif str(item.get("promotion_action") or "") == "retire":
                docket_status = "retirement_candidate"

            items.append(
                {
                    **item,
                    "experiment_id": experiment.get("experiment_id"),
                    "strategy_id": experiment.get("strategy_id"),
                    "model_id": model.get("model_id"),
                    "model_state": model.get("state"),
                    "lineage_ready": bool(experiment or model),
                    "docket_status": docket_status,
                }
            )

        return {
            "status": "ok",
            "run_id": agenda.get("run_id"),
            "cycle_id": agenda.get("cycle_id"),
            "mode": agenda.get("mode"),
            "items": items,
            "decision_summary": {
                "alpha_count": len(items),
                "lineage_ready_items": sum(1 for item in items if item.get("lineage_ready")),
                "promotion_candidate_count": sum(1 for item in items if item.get("docket_status") == "promotion_candidate"),
                "shadow_candidate_count": sum(1 for item in items if item.get("docket_status") == "shadow_candidate"),
                "demotion_candidate_count": sum(1 for item in items if item.get("docket_status") == "demotion_candidate"),
                "retirement_candidate_count": sum(1 for item in items if item.get("docket_status") == "retirement_candidate"),
            },
            "control_context": agenda.get("control_context"),
            "as_of": agenda.get("as_of"),
        }

    def review_queues_latest(self, limit: int = 20) -> dict[str, Any]:
        docket = self.promotion_candidate_docket_latest(limit=limit)
        items: list[dict[str, Any]] = []

        for item in list(docket.get("items") or []):
            docket_status = str(item.get("docket_status") or "queued_for_review")
            review_queue = "research_backlog"
            next_review_action = "hold_for_more_evidence"

            if docket_status == "promotion_candidate":
                review_queue = "promotion_review"
                next_review_action = "evaluate_for_promotion"
            elif docket_status == "shadow_candidate":
                review_queue = "shadow_review"
                next_review_action = "evaluate_for_shadow"
            elif docket_status == "demotion_candidate":
                review_queue = "demotion_review"
                next_review_action = "evaluate_for_demotion"
            elif docket_status == "retirement_candidate":
                review_queue = "retirement_review"
                next_review_action = "evaluate_for_retirement"

            queue_priority = str(item.get("review_priority") or "normal")
            if review_queue == "promotion_review":
                queue_priority = "immediate"
            elif review_queue in {"shadow_review", "demotion_review"} and queue_priority == "normal":
                queue_priority = "high"

            items.append(
                {
                    **item,
                    "review_queue": review_queue,
                    "next_review_action": next_review_action,
                    "queue_priority": queue_priority,
                }
            )

        return {
            "status": "ok",
            "run_id": docket.get("run_id"),
            "cycle_id": docket.get("cycle_id"),
            "mode": docket.get("mode"),
            "items": items,
            "queue_summary": {
                "alpha_count": len(items),
                "promotion_review_count": sum(1 for item in items if item.get("review_queue") == "promotion_review"),
                "shadow_review_count": sum(1 for item in items if item.get("review_queue") == "shadow_review"),
                "demotion_review_count": sum(1 for item in items if item.get("review_queue") == "demotion_review"),
                "retirement_review_count": sum(1 for item in items if item.get("review_queue") == "retirement_review"),
                "research_backlog_count": sum(1 for item in items if item.get("review_queue") == "research_backlog"),
            },
            "control_context": docket.get("control_context"),
            "as_of": docket.get("as_of"),
        }

    def review_board_slate_latest(self, limit: int = 20) -> dict[str, Any]:
        queues = self.review_queues_latest(limit=limit)
        items: list[dict[str, Any]] = []

        for item in list(queues.get("items") or []):
            review_queue = str(item.get("review_queue") or "research_backlog")
            lineage_ready = bool(item.get("lineage_ready"))
            selection_score = float(item.get("selection_score", 0.0) or 0.0)

            board_decision = "hold"
            board_rationale = "await_more_board_evidence"

            if review_queue == "promotion_review":
                if lineage_ready:
                    board_decision = "approve_promotion_review"
                    board_rationale = "promotion_queue_with_lineage"
                else:
                    board_decision = "hold"
                    board_rationale = "promotion_queue_missing_lineage"
            elif review_queue == "shadow_review":
                if lineage_ready:
                    board_decision = "approve_shadow_review"
                    board_rationale = "shadow_queue_with_lineage"
                else:
                    board_decision = "hold"
                    board_rationale = "shadow_queue_missing_lineage"
            elif review_queue == "demotion_review":
                board_decision = "approve_demotion_review"
                board_rationale = "demotion_candidate_requires_board_confirmation"
            elif review_queue == "retirement_review":
                board_decision = "approve_retirement_review"
                board_rationale = "retirement_candidate_requires_board_confirmation"
            elif review_queue == "research_backlog" and selection_score < self.RETIRE_THRESHOLD:
                board_decision = "return_to_research"
                board_rationale = "low_score_backlog_candidate"

            board_priority = str(item.get("queue_priority") or "normal")
            if board_decision == "approve_promotion_review":
                board_priority = "immediate"
            elif board_decision in {"approve_shadow_review", "approve_demotion_review"} and board_priority == "normal":
                board_priority = "high"

            items.append(
                {
                    **item,
                    "board_decision": board_decision,
                    "board_rationale": board_rationale,
                    "board_priority": board_priority,
                }
            )

        return {
            "status": "ok",
            "run_id": queues.get("run_id"),
            "cycle_id": queues.get("cycle_id"),
            "mode": queues.get("mode"),
            "items": items,
            "board_summary": {
                "alpha_count": len(items),
                "approve_promotion_review_count": sum(1 for item in items if item.get("board_decision") == "approve_promotion_review"),
                "approve_shadow_review_count": sum(1 for item in items if item.get("board_decision") == "approve_shadow_review"),
                "approve_demotion_review_count": sum(1 for item in items if item.get("board_decision") == "approve_demotion_review"),
                "approve_retirement_review_count": sum(1 for item in items if item.get("board_decision") == "approve_retirement_review"),
                "hold_count": sum(1 for item in items if item.get("board_decision") == "hold"),
                "return_to_research_count": sum(1 for item in items if item.get("board_decision") == "return_to_research"),
            },
            "control_context": queues.get("control_context"),
            "as_of": queues.get("as_of"),
        }

    def deterministic_review_outcomes_latest(self, limit: int = 20) -> dict[str, Any]:
        board = self.review_board_slate_latest(limit=limit)
        items: list[dict[str, Any]] = []

        for item in list(board.get("items") or []):
            board_decision = str(item.get("board_decision") or "hold")
            previous_review_status = str(item.get("review_queue") or "research_backlog")
            resolved_review_outcome = "needs_more_evidence"
            outcome_reason_code = "board_hold_pending_more_evidence"
            downstream_target_state = "candidate"

            if board_decision == "approve_promotion_review":
                resolved_review_outcome = "promote"
                outcome_reason_code = "approved_for_promotion"
                downstream_target_state = "promoted"
            elif board_decision == "approve_shadow_review":
                resolved_review_outcome = "shadow"
                outcome_reason_code = "approved_for_shadow"
                downstream_target_state = "shadow"
            elif board_decision == "approve_demotion_review":
                resolved_review_outcome = "reject"
                outcome_reason_code = "approved_for_demotion"
                downstream_target_state = "candidate"
            elif board_decision == "approve_retirement_review":
                resolved_review_outcome = "retire"
                outcome_reason_code = "approved_for_retirement"
                downstream_target_state = "retired"
            elif board_decision == "return_to_research":
                resolved_review_outcome = "defer"
                outcome_reason_code = "returned_to_research_backlog"
                downstream_target_state = "candidate"

            items.append(
                {
                    **item,
                    "previous_review_status": previous_review_status,
                    "resolved_review_outcome": resolved_review_outcome,
                    "outcome_reason_code": outcome_reason_code,
                    "downstream_target_state": downstream_target_state,
                }
            )

        return {
            "status": "ok",
            "run_id": board.get("run_id"),
            "cycle_id": board.get("cycle_id"),
            "mode": board.get("mode"),
            "items": items,
            "outcome_summary": {
                "alpha_count": len(items),
                "promote_count": sum(1 for item in items if item.get("resolved_review_outcome") == "promote"),
                "shadow_count": sum(1 for item in items if item.get("resolved_review_outcome") == "shadow"),
                "defer_count": sum(1 for item in items if item.get("resolved_review_outcome") == "defer"),
                "reject_count": sum(1 for item in items if item.get("resolved_review_outcome") == "reject"),
                "retire_count": sum(1 for item in items if item.get("resolved_review_outcome") == "retire"),
                "needs_more_evidence_count": sum(1 for item in items if item.get("resolved_review_outcome") == "needs_more_evidence"),
            },
            "control_context": board.get("control_context"),
            "as_of": board.get("as_of"),
        }

    def persisted_governed_state_transitions_latest(self, limit: int = 20) -> dict[str, Any]:
        outcomes = self.deterministic_review_outcomes_latest(limit=limit)
        created_at = utc_now_iso()
        items: list[dict[str, Any]] = []

        for item in list(outcomes.get("items") or []):
            alpha_id = str(item.get("alpha_id") or "")
            current_alpha = self.store.fetchone_dict(
                "SELECT * FROM alpha_registry WHERE alpha_id=? ORDER BY created_at DESC LIMIT 1",
                [alpha_id],
            ) or {}
            prior_state = str(current_alpha.get("state") or "candidate")
            resolved_review_outcome = str(item.get("resolved_review_outcome") or "needs_more_evidence")

            new_state = prior_state
            transition_event_type = "review_outcome_recorded"
            if resolved_review_outcome == "promote":
                new_state = "promoted"
                transition_event_type = "promote"
            elif resolved_review_outcome == "shadow":
                new_state = "shadow"
                transition_event_type = "shadow"
            elif resolved_review_outcome == "retire":
                new_state = "retired"
                transition_event_type = "retire"
            elif resolved_review_outcome == "reject":
                new_state = "rejected"
                transition_event_type = "reject"
            elif resolved_review_outcome == "defer":
                new_state = "candidate"
                transition_event_type = "defer"
            elif resolved_review_outcome == "needs_more_evidence":
                new_state = prior_state
                transition_event_type = "needs_more_evidence"

            transition_id = new_cycle_id()
            authority = "research_promotion_intelligence_rpi06"

            if alpha_id:
                self.store.append(
                    "alpha_registry",
                    {
                        "alpha_id": alpha_id,
                        "created_at": created_at,
                        "alpha_family": current_alpha.get("alpha_family", "custom"),
                        "factor_type": current_alpha.get("factor_type", "hybrid"),
                        "horizon": current_alpha.get("horizon", "short"),
                        "turnover_profile": current_alpha.get("turnover_profile", "medium"),
                        "feature_dependencies_json": current_alpha.get("feature_dependencies_json") or self.store.to_json([]),
                        "risk_profile": current_alpha.get("risk_profile", "balanced"),
                        "execution_sensitivity": float(current_alpha.get("execution_sensitivity", 0.0) or 0.0),
                        "state": new_state,
                        "source": authority,
                        "notes": str(item.get("outcome_reason_code") or "rpi06_transition"),
                    },
                )
                self.store.append(
                    "alpha_status_events",
                    {
                        "event_id": transition_id,
                        "created_at": created_at,
                        "alpha_id": alpha_id,
                        "event_type": transition_event_type,
                        "from_state": prior_state,
                        "to_state": new_state,
                        "reason": str(item.get("outcome_reason_code") or "rpi06_transition"),
                    },
                )
                self.store.append(
                    "alpha_library",
                    {
                        "library_id": new_cycle_id(),
                        "created_at": created_at,
                        "alpha_id": alpha_id,
                        "alpha_family": current_alpha.get("alpha_family", "custom"),
                        "factor_type": current_alpha.get("factor_type", "hybrid"),
                        "state": new_state,
                        "rank_score": float(item.get("selection_score", 0.0) or 0.0),
                        "usage_count": int((self.store.fetchone_dict(
                            "SELECT usage_count FROM alpha_library WHERE alpha_id=? ORDER BY created_at DESC LIMIT 1",
                            [alpha_id],
                        ) or {}).get("usage_count") or 0),
                        "tags_json": (self.store.fetchone_dict(
                            "SELECT tags_json FROM alpha_library WHERE alpha_id=? ORDER BY created_at DESC LIMIT 1",
                            [alpha_id],
                        ) or {}).get("tags_json") or self.store.to_json([
                            current_alpha.get("alpha_family", "custom"),
                            current_alpha.get("factor_type", "hybrid"),
                        ]),
                    },
                )

            items.append(
                {
                    **item,
                    "transition_id": transition_id,
                    "prior_governed_state": prior_state,
                    "new_governed_state": new_state,
                    "transition_timestamp": created_at,
                    "transition_source_packet": "RPI-06",
                    "authority_surface": authority,
                }
            )

        return {
            "status": "ok",
            "run_id": outcomes.get("run_id"),
            "cycle_id": outcomes.get("cycle_id"),
            "mode": outcomes.get("mode"),
            "items": items,
            "transition_summary": {
                "alpha_count": len(items),
                "promoted_state_count": sum(1 for item in items if item.get("new_governed_state") == "promoted"),
                "shadow_state_count": sum(1 for item in items if item.get("new_governed_state") == "shadow"),
                "retired_state_count": sum(1 for item in items if item.get("new_governed_state") == "retired"),
                "rejected_state_count": sum(1 for item in items if item.get("new_governed_state") == "rejected"),
            },
            "control_context": outcomes.get("control_context"),
            "as_of": outcomes.get("as_of"),
        }
