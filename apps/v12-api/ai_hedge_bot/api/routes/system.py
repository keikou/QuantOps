from __future__ import annotations

from fastapi import APIRouter
from ai_hedge_bot.alpha_attribution.attribution_service import AlphaAttributionService
from ai_hedge_bot.alpha_capacity.capacity_service import AlphaCapacityService
from ai_hedge_bot.alpha_feedback.feedback_service import AlphaFeedbackService
from ai_hedge_bot.alpha_retirement.retirement_service import AlphaRetirementService
from ai_hedge_bot.alpha_weighting.weighting_service import AlphaWeightingService
from ai_hedge_bot.alpha_ensemble.ensemble_service import AlphaEnsembleService
from ai_hedge_bot.alpha_evaluation.evaluation_service import AlphaEvaluationService
from ai_hedge_bot.alpha_validation.validation_service import AlphaValidationService
from ai_hedge_bot.data_integrity.data_integrity_service import DataIntegrityService
from ai_hedge_bot.execution_health.execution_health_service import ExecutionHealthService
from ai_hedge_bot.operational_governance.operational_governance_service import OperationalGovernanceService
from ai_hedge_bot.operational_risk.operational_risk_service import OperationalRiskService
from ai_hedge_bot.alpha_synthesis.alpha_synthesis_service import AlphaSynthesisService
from ai_hedge_bot.services.autonomous_alpha_expansion_strategy_generation_intelligence_service import (
    AutonomousAlphaExpansionStrategyGenerationIntelligenceService,
)
from ai_hedge_bot.app.container import CONTAINER
from ai_hedge_bot.services.deployment_rollout_intelligence_service import (
    DeploymentRolloutIntelligenceService,
)
from ai_hedge_bot.services.hardening_architect_handoff_service import HardeningArchitectHandoffService
from ai_hedge_bot.services.hardening_evidence_snapshot_service import HardeningEvidenceSnapshotService
from ai_hedge_bot.services.hardening_handover_manifest_service import HardeningHandoverManifestService
from ai_hedge_bot.services.hardening_status_service import HardeningStatusService
from ai_hedge_bot.services.live_capital_control_adaptive_runtime_allocation_service import (
    LiveCapitalControlAdaptiveRuntimeAllocationService,
)
from ai_hedge_bot.services.meta_portfolio_intelligence_cross_strategy_capital_allocation_service import (
    MetaPortfolioIntelligenceCrossStrategyCapitalAllocationService,
)
from ai_hedge_bot.services.operator_diagnostic_bundle_service import OperatorDiagnosticBundleService
from ai_hedge_bot.services.policy_optimization_meta_control_learning_service import (
    PolicyOptimizationMetaControlLearningService,
)
from ai_hedge_bot.services.recovery_replay_diagnostic_bundle_service import RecoveryReplayDiagnosticBundleService
from ai_hedge_bot.services.resume_operator_packet_service import ResumeOperatorPacketService
from ai_hedge_bot.services.strategy_evolution_regime_adaptation_intelligence_service import (
    StrategyEvolutionRegimeAdaptationIntelligenceService,
)
from ai_hedge_bot.services.system_level_learning_feedback_integration_service import (
    SystemLevelLearningFeedbackIntegrationService,
)

router = APIRouter(tags=['system'])
_deployment_rollout = DeploymentRolloutIntelligenceService()
_hardening_architect_handoff = HardeningArchitectHandoffService()
_hardening_snapshot = HardeningEvidenceSnapshotService()
_hardening_manifest = HardeningHandoverManifestService()
_hardening_status = HardeningStatusService()
_live_capital_control = LiveCapitalControlAdaptiveRuntimeAllocationService()
_meta_portfolio = MetaPortfolioIntelligenceCrossStrategyCapitalAllocationService()
_operator_bundle = OperatorDiagnosticBundleService()
_policy_optimization = PolicyOptimizationMetaControlLearningService()
_recovery_replay_bundle = RecoveryReplayDiagnosticBundleService()
_resume_operator_packet = ResumeOperatorPacketService()
_strategy_evolution = StrategyEvolutionRegimeAdaptationIntelligenceService()
_system_learning_feedback = SystemLevelLearningFeedbackIntegrationService()
_autonomous_alpha_expansion = AutonomousAlphaExpansionStrategyGenerationIntelligenceService()
_alpha_synthesis = AlphaSynthesisService()
_alpha_evaluation = AlphaEvaluationService()
_alpha_validation = AlphaValidationService()
_alpha_ensemble = AlphaEnsembleService()
_alpha_attribution = AlphaAttributionService()
_alpha_capacity = AlphaCapacityService()
_alpha_weighting = AlphaWeightingService()
_alpha_retirement = AlphaRetirementService()
_alpha_feedback = AlphaFeedbackService()
_operational_risk = OperationalRiskService()
_execution_health = ExecutionHealthService()
_data_integrity = DataIntegrityService()
_operational_governance = OperationalGovernanceService()


def _payload() -> dict:
    return {
        'status': 'ok',
        'mode': CONTAINER.mode.value,
        'symbols': CONTAINER.config.symbols,
        'phase': 'H',
        'sprint': 4,
    }

@router.get('/system/health')
def system_health() -> dict:
    return _payload()

@router.get('/health')
def legacy_health() -> dict:
    return _payload()


@router.post('/system/hardening-architect-handoff/save')
def save_hardening_architect_handoff() -> dict:
    return _hardening_architect_handoff.save()


@router.get('/system/hardening-architect-handoff/latest')
def latest_hardening_architect_handoff() -> dict:
    return _hardening_architect_handoff.latest()


@router.post('/system/resume-operator-packet/save')
def save_resume_operator_packet() -> dict:
    return _resume_operator_packet.save()


@router.get('/system/resume-operator-packet/latest')
def latest_resume_operator_packet() -> dict:
    return _resume_operator_packet.latest()


@router.get('/system/hardening-handover-manifest')
def hardening_handover_manifest() -> dict:
    return _hardening_manifest.build()


@router.post('/system/hardening-evidence-snapshot/save')
def save_hardening_evidence_snapshot() -> dict:
    return _hardening_snapshot.save()


@router.get('/system/hardening-evidence-snapshot/latest')
def latest_hardening_evidence_snapshot() -> dict:
    return _hardening_snapshot.load()


@router.get('/system/hardening-status')
def hardening_status() -> dict:
    return _hardening_status.build()


@router.get('/system/operator-diagnostic-bundle')
def operator_diagnostic_bundle() -> dict:
    return _operator_bundle.build()


@router.get('/system/recovery-replay-diagnostic-bundle')
def recovery_replay_diagnostic_bundle() -> dict:
    return _recovery_replay_bundle.build()


@router.get('/system/learning-feedback/latest')
def system_learning_feedback_latest(limit: int = 20) -> dict:
    return _system_learning_feedback.latest(limit=limit)


@router.get('/system/learning-policy-updates/latest')
def system_learning_policy_updates_latest(limit: int = 20) -> dict:
    return _system_learning_feedback.policy_updates_latest(limit=limit)


@router.get('/system/learning-policy-state/latest')
def system_learning_policy_state_latest(limit: int = 20) -> dict:
    return _system_learning_feedback.persisted_policy_state_latest(limit=limit)


@router.get('/system/learning-resolved-overrides/latest')
def system_learning_resolved_overrides_latest(limit: int = 20) -> dict:
    return _system_learning_feedback.resolved_overrides_latest(limit=limit)


@router.get('/system/learning-applied-consumption/latest')
def system_learning_applied_consumption_latest(limit: int = 20) -> dict:
    return _system_learning_feedback.applied_override_consumption_latest(limit=limit)


@router.get('/system/policy-effectiveness/latest')
def system_policy_effectiveness_latest(limit: int = 20) -> dict:
    return _policy_optimization.latest(limit=limit)


@router.get('/system/policy-tuning/latest')
def system_policy_tuning_latest(limit: int = 20) -> dict:
    return _policy_optimization.tuning_recommendations_latest(limit=limit)


@router.get('/system/meta-policy-state/latest')
def system_meta_policy_state_latest(limit: int = 20) -> dict:
    return _policy_optimization.persisted_meta_policy_state_latest(limit=limit)


@router.get('/system/meta-policy-consumption/latest')
def system_meta_policy_consumption_latest(limit: int = 20) -> dict:
    return _policy_optimization.applied_tuning_consumption_latest(limit=limit)


@router.get('/system/meta-policy-effectiveness/latest')
def system_meta_policy_effectiveness_latest(limit: int = 20) -> dict:
    return _policy_optimization.outcome_effectiveness_latest(limit=limit)


@router.get('/system/deployment-rollout-decision/latest')
def system_deployment_rollout_decision_latest(limit: int = 20) -> dict:
    return _deployment_rollout.latest(limit=limit)


@router.get('/system/deployment-rollout-candidate-docket/latest')
def system_deployment_rollout_candidate_docket_latest(limit: int = 20) -> dict:
    return _deployment_rollout.candidate_docket_latest(limit=limit)


@router.get('/system/deployment-rollout-state/latest')
def system_deployment_rollout_state_latest(limit: int = 20) -> dict:
    return _deployment_rollout.persisted_rollout_state_latest(limit=limit)


@router.get('/system/deployment-rollout-consumption/latest')
def system_deployment_rollout_consumption_latest(limit: int = 20) -> dict:
    return _deployment_rollout.applied_rollout_consumption_latest(limit=limit)


@router.get('/system/deployment-rollout-effectiveness/latest')
def system_deployment_rollout_effectiveness_latest(limit: int = 20) -> dict:
    return _deployment_rollout.rollout_outcome_effectiveness_latest(limit=limit)


@router.get('/system/live-capital-control/latest')
def system_live_capital_control_latest(limit: int = 20) -> dict:
    return _live_capital_control.latest(limit=limit)


@router.get('/system/live-capital-adjustment-decision/latest')
def system_live_capital_adjustment_decision_latest(limit: int = 20) -> dict:
    return _live_capital_control.adjustment_decision_latest(limit=limit)


@router.get('/system/live-capital-control-state/latest')
def system_live_capital_control_state_latest(limit: int = 20) -> dict:
    return _live_capital_control.control_state_latest(limit=limit)


@router.get('/system/live-capital-control-consumption/latest')
def system_live_capital_control_consumption_latest(limit: int = 20) -> dict:
    return _live_capital_control.control_consumption_latest(limit=limit)


@router.get('/system/live-capital-control-effectiveness/latest')
def system_live_capital_control_effectiveness_latest(limit: int = 20) -> dict:
    return _live_capital_control.control_effectiveness_latest(limit=limit)


@router.get('/system/meta-portfolio-allocation/latest')
def system_meta_portfolio_allocation_latest(limit: int = 20) -> dict:
    return _meta_portfolio.latest(limit=limit)


@router.get('/system/meta-portfolio-decision/latest')
def system_meta_portfolio_decision_latest(limit: int = 20) -> dict:
    return _meta_portfolio.decision_latest(limit=limit)


@router.get('/system/meta-portfolio-state/latest')
def system_meta_portfolio_state_latest(limit: int = 20) -> dict:
    return _meta_portfolio.state_latest(limit=limit)


@router.get('/system/meta-portfolio-flow/latest')
def system_meta_portfolio_flow_latest(limit: int = 20) -> dict:
    return _meta_portfolio.flow_latest(limit=limit)


@router.get('/system/meta-portfolio-efficiency/latest')
def system_meta_portfolio_efficiency_latest(limit: int = 20) -> dict:
    return _meta_portfolio.efficiency_latest(limit=limit)


@router.get('/system/regime-state/latest')
def system_regime_state_latest(limit: int = 20) -> dict:
    return _strategy_evolution.latest(limit=limit)


@router.get('/system/strategy-regime-compatibility/latest')
def system_strategy_regime_compatibility_latest(limit: int = 20) -> dict:
    return _strategy_evolution.strategy_regime_compatibility_latest(limit=limit)


@router.get('/system/strategy-gating-decision/latest')
def system_strategy_gating_decision_latest(limit: int = 20) -> dict:
    return _strategy_evolution.strategy_gating_decision_latest(limit=limit)


@router.get('/system/regime-transition-detection/latest')
def system_regime_transition_detection_latest(limit: int = 20) -> dict:
    return _strategy_evolution.regime_transition_detection_latest(limit=limit)


@router.get('/system/strategy-survival-analysis/latest')
def system_strategy_survival_analysis_latest(limit: int = 20) -> dict:
    return _strategy_evolution.strategy_survival_analysis_latest(limit=limit)


@router.get('/system/alpha-discovery-candidates/latest')
def system_alpha_discovery_candidates_latest(limit: int = 20) -> dict:
    return _autonomous_alpha_expansion.alpha_discovery_candidates_latest(limit=limit)


@router.get('/system/alpha-validation-results/latest')
def system_alpha_validation_results_latest(limit: int = 20) -> dict:
    return _autonomous_alpha_expansion.alpha_validation_results_latest(limit=limit)


@router.get('/system/alpha-admission-decision/latest')
def system_alpha_admission_decision_latest(limit: int = 20) -> dict:
    return _autonomous_alpha_expansion.alpha_admission_decision_latest(limit=limit)


@router.get('/system/alpha-lifecycle-state/latest')
def system_alpha_lifecycle_state_latest(limit: int = 20) -> dict:
    return _autonomous_alpha_expansion.alpha_lifecycle_state_latest(limit=limit)


@router.get('/system/alpha-inventory-health/latest')
def system_alpha_inventory_health_latest(limit: int = 20) -> dict:
    return _autonomous_alpha_expansion.alpha_inventory_health_latest(limit=limit)


@router.get('/system/alpha-generation-agenda/latest')
def system_alpha_generation_agenda_latest(limit: int = 20) -> dict:
    return _autonomous_alpha_expansion.alpha_generation_agenda_latest(limit=limit)


@router.get('/system/alpha-experiment-docket/latest')
def system_alpha_experiment_docket_latest(limit: int = 20) -> dict:
    return _autonomous_alpha_expansion.alpha_experiment_docket_latest(limit=limit)


@router.get('/system/alpha-replacement-decision/latest')
def system_alpha_replacement_decision_latest(limit: int = 20) -> dict:
    return _autonomous_alpha_expansion.alpha_replacement_decision_latest(limit=limit)


@router.get('/system/alpha-replacement-state/latest')
def system_alpha_replacement_state_latest(limit: int = 20) -> dict:
    return _autonomous_alpha_expansion.alpha_replacement_state_latest(limit=limit)


@router.get('/system/alpha-expansion-effectiveness/latest')
def system_alpha_expansion_effectiveness_latest(limit: int = 20) -> dict:
    return _autonomous_alpha_expansion.alpha_expansion_effectiveness_latest(limit=limit)


@router.get('/system/alpha-runtime-deployment-candidates/latest')
def system_alpha_runtime_deployment_candidates_latest(limit: int = 20) -> dict:
    return _autonomous_alpha_expansion.alpha_runtime_deployment_candidates_latest(limit=limit)


@router.get('/system/alpha-runtime-governance-feedback/latest')
def system_alpha_runtime_governance_feedback_latest(limit: int = 20) -> dict:
    return _autonomous_alpha_expansion.alpha_runtime_governance_feedback_latest(limit=limit)


@router.get('/system/alpha-runtime-rollback-response/latest')
def system_alpha_runtime_rollback_response_latest(limit: int = 20) -> dict:
    return _autonomous_alpha_expansion.alpha_runtime_rollback_response_latest(limit=limit)


@router.get('/system/alpha-runtime-champion-challenger/latest')
def system_alpha_runtime_champion_challenger_latest(limit: int = 20) -> dict:
    return _autonomous_alpha_expansion.alpha_runtime_champion_challenger_latest(limit=limit)


@router.get('/system/alpha-runtime-expansion-effectiveness/latest')
def system_alpha_runtime_expansion_effectiveness_latest(limit: int = 20) -> dict:
    return _autonomous_alpha_expansion.alpha_runtime_expansion_effectiveness_latest(limit=limit)


@router.get('/system/alpha-next-cycle-learning-input/latest')
def system_alpha_next_cycle_learning_input_latest(limit: int = 20) -> dict:
    return _autonomous_alpha_expansion.alpha_next_cycle_learning_input_latest(limit=limit)


@router.get('/system/alpha-next-cycle-policy-bridge/latest')
def system_alpha_next_cycle_policy_bridge_latest(limit: int = 20) -> dict:
    return _autonomous_alpha_expansion.alpha_next_cycle_policy_bridge_latest(limit=limit)


@router.get('/system/alpha-regime-adaptation-input/latest')
def system_alpha_regime_adaptation_input_latest(limit: int = 20) -> dict:
    return _autonomous_alpha_expansion.alpha_regime_adaptation_input_latest(limit=limit)


@router.get('/system/alpha-universe-refresh-priorities/latest')
def system_alpha_universe_refresh_priorities_latest(limit: int = 20) -> dict:
    return _autonomous_alpha_expansion.alpha_universe_refresh_priorities_latest(limit=limit)


@router.get('/system/alpha-expansion-learning-effectiveness/latest')
def system_alpha_expansion_learning_effectiveness_latest(limit: int = 20) -> dict:
    return _autonomous_alpha_expansion.alpha_expansion_learning_effectiveness_latest(limit=limit)


@router.get('/system/alpha-promotion-bridge/latest')
def system_alpha_promotion_bridge_latest(limit: int = 20) -> dict:
    return _autonomous_alpha_expansion.alpha_promotion_bridge_latest(limit=limit)


@router.get('/system/alpha-family-capital-intent/latest')
def system_alpha_family_capital_intent_latest(limit: int = 20) -> dict:
    return _autonomous_alpha_expansion.alpha_family_capital_intent_latest(limit=limit)


@router.get('/system/alpha-portfolio-intake-queue/latest')
def system_alpha_portfolio_intake_queue_latest(limit: int = 20) -> dict:
    return _autonomous_alpha_expansion.alpha_portfolio_intake_queue_latest(limit=limit)


@router.get('/system/alpha-governed-universe-state/latest')
def system_alpha_governed_universe_state_latest(limit: int = 20) -> dict:
    return _autonomous_alpha_expansion.alpha_governed_universe_state_latest(limit=limit)


@router.get('/system/alpha-strategy-factory-readiness/latest')
def system_alpha_strategy_factory_readiness_latest(limit: int = 20) -> dict:
    return _autonomous_alpha_expansion.alpha_strategy_factory_readiness_latest(limit=limit)


@router.get('/system/alpha-synthesis-candidates/latest')
def system_alpha_synthesis_candidates_latest(limit: int = 20) -> dict:
    return _alpha_synthesis.alpha_synthesis_candidates_latest(limit=limit)


@router.get('/system/alpha-structure-search-state/latest')
def system_alpha_structure_search_state_latest(limit: int = 20) -> dict:
    return _alpha_synthesis.alpha_structure_search_state_latest(limit=limit)


@router.get('/system/alpha-novelty-evaluation/latest')
def system_alpha_novelty_evaluation_latest(limit: int = 20) -> dict:
    return _alpha_synthesis.alpha_novelty_evaluation_latest(limit=limit)


@router.get('/system/alpha-expression-library/latest')
def system_alpha_expression_library_latest(limit: int = 20) -> dict:
    return _alpha_synthesis.alpha_expression_library_latest(limit=limit)


@router.get('/system/alpha-synthesis-effectiveness/latest')
def system_alpha_synthesis_effectiveness_latest(limit: int = 20) -> dict:
    return _alpha_synthesis.alpha_synthesis_effectiveness_latest(limit=limit)


@router.get('/system/alpha-parent-candidates/latest')
def system_alpha_parent_candidates_latest(limit: int = 20) -> dict:
    return _alpha_synthesis.alpha_parent_candidates_latest(limit=limit)


@router.get('/system/alpha-mutation-candidates/latest')
def system_alpha_mutation_candidates_latest(limit: int = 20) -> dict:
    return _alpha_synthesis.alpha_mutation_candidates_latest(limit=limit)


@router.get('/system/alpha-crossover-candidates/latest')
def system_alpha_crossover_candidates_latest(limit: int = 20) -> dict:
    return _alpha_synthesis.alpha_crossover_candidates_latest(limit=limit)


@router.get('/system/alpha-evolution-search-state/latest')
def system_alpha_evolution_search_state_latest(limit: int = 20) -> dict:
    return _alpha_synthesis.alpha_evolution_search_state_latest(limit=limit)


@router.get('/system/alpha-evolution-effectiveness/latest')
def system_alpha_evolution_effectiveness_latest(limit: int = 20) -> dict:
    return _alpha_synthesis.alpha_evolution_effectiveness_latest(limit=limit)


@router.get('/system/alpha-regime-synthesis-agenda/latest')
def system_alpha_regime_synthesis_agenda_latest(limit: int = 20) -> dict:
    return _alpha_synthesis.alpha_regime_synthesis_agenda_latest(limit=limit)


@router.get('/system/alpha-regime-targeted-candidates/latest')
def system_alpha_regime_targeted_candidates_latest(limit: int = 20) -> dict:
    return _alpha_synthesis.alpha_regime_targeted_candidates_latest(limit=limit)


@router.get('/system/alpha-regime-fit-evaluation/latest')
def system_alpha_regime_fit_evaluation_latest(limit: int = 20) -> dict:
    return _alpha_synthesis.alpha_regime_fit_evaluation_latest(limit=limit)


@router.get('/system/alpha-regime-expression-map/latest')
def system_alpha_regime_expression_map_latest(limit: int = 20) -> dict:
    return _alpha_synthesis.alpha_regime_expression_map_latest(limit=limit)


@router.get('/system/alpha-regime-synthesis-effectiveness/latest')
def system_alpha_regime_synthesis_effectiveness_latest(limit: int = 20) -> dict:
    return _alpha_synthesis.alpha_regime_synthesis_effectiveness_latest(limit=limit)


@router.get('/system/alpha-hypothesis-agenda/latest')
def system_alpha_hypothesis_agenda_latest(limit: int = 20) -> dict:
    return _alpha_synthesis.alpha_hypothesis_agenda_latest(limit=limit)


@router.get('/system/alpha-llm-hypothesis-prompts/latest')
def system_alpha_llm_hypothesis_prompts_latest(limit: int = 20) -> dict:
    return _alpha_synthesis.alpha_llm_hypothesis_prompts_latest(limit=limit)


@router.get('/system/alpha-llm-translation-candidates/latest')
def system_alpha_llm_translation_candidates_latest(limit: int = 20) -> dict:
    return _alpha_synthesis.alpha_llm_translation_candidates_latest(limit=limit)


@router.get('/system/alpha-hypothesis-critique/latest')
def system_alpha_hypothesis_critique_latest(limit: int = 20) -> dict:
    return _alpha_synthesis.alpha_hypothesis_critique_latest(limit=limit)


@router.get('/system/alpha-hypothesis-effectiveness/latest')
def system_alpha_hypothesis_effectiveness_latest(limit: int = 20) -> dict:
    return _alpha_synthesis.alpha_hypothesis_effectiveness_latest(limit=limit)


@router.get('/system/alpha-hypothesis-feedback-queue/latest')
def system_alpha_hypothesis_feedback_queue_latest(limit: int = 20) -> dict:
    return _alpha_synthesis.alpha_hypothesis_feedback_queue_latest(limit=limit)


@router.get('/system/alpha-hypothesis-prompt-tuning/latest')
def system_alpha_hypothesis_prompt_tuning_latest(limit: int = 20) -> dict:
    return _alpha_synthesis.alpha_hypothesis_prompt_tuning_latest(limit=limit)


@router.get('/system/alpha-synthesis-policy-updates/latest')
def system_alpha_synthesis_policy_updates_latest(limit: int = 20) -> dict:
    return _alpha_synthesis.alpha_synthesis_policy_updates_latest(limit=limit)


@router.get('/system/alpha-feedback-learning-state/latest')
def system_alpha_feedback_learning_state_latest(limit: int = 20) -> dict:
    return _alpha_synthesis.alpha_feedback_learning_state_latest(limit=limit)


@router.get('/system/alpha-feedback-optimization-effectiveness/latest')
def system_alpha_feedback_optimization_effectiveness_latest(limit: int = 20) -> dict:
    return _alpha_synthesis.alpha_feedback_optimization_effectiveness_latest(limit=limit)


@router.get('/system/alpha-evaluation/latest')
def system_alpha_evaluation_latest(limit: int = 20) -> dict:
    return _alpha_evaluation.latest(limit=limit)


@router.get('/system/alpha-decay-analysis/latest')
def system_alpha_decay_analysis_latest(limit: int = 20) -> dict:
    return _alpha_evaluation.alpha_decay_analysis_latest(limit=limit)


@router.get('/system/alpha-correlation-matrix/latest')
def system_alpha_correlation_matrix_latest(limit: int = 20) -> dict:
    return _alpha_evaluation.alpha_correlation_matrix_latest(limit=limit)


@router.get('/system/alpha-robustness-ranking/latest')
def system_alpha_robustness_ranking_latest(limit: int = 20) -> dict:
    return _alpha_evaluation.alpha_robustness_ranking_latest(limit=limit)


@router.get('/system/alpha-selection-decisions/latest')
def system_alpha_selection_decisions_latest(limit: int = 20) -> dict:
    return _alpha_evaluation.alpha_selection_decisions_latest(limit=limit)


@router.post('/system/alpha-evaluation/run')
def system_alpha_evaluation_run(limit: int = 20) -> dict:
    return _alpha_evaluation.run(limit=limit)


@router.get('/system/alpha-evaluation/candidate/{alpha_id}')
def system_alpha_evaluation_candidate(alpha_id: str) -> dict:
    return _alpha_evaluation.alpha_evaluation_candidate(alpha_id)


@router.post('/system/alpha-walk-forward/run')
def system_alpha_walk_forward_run(limit: int = 20) -> dict:
    return _alpha_validation.run(limit=limit)


@router.get('/system/alpha-walk-forward/latest')
def system_alpha_walk_forward_latest(limit: int = 20) -> dict:
    return _alpha_validation.latest(limit=limit)


@router.get('/system/alpha-walk-forward/candidate/{alpha_id}')
def system_alpha_walk_forward_candidate(alpha_id: str) -> dict:
    return _alpha_validation.alpha_walk_forward_candidate(alpha_id)


@router.get('/system/alpha-oos-validation/latest')
def system_alpha_oos_validation_latest(limit: int = 20) -> dict:
    return _alpha_validation.alpha_oos_validation_latest(limit=limit)


@router.get('/system/alpha-validation-decisions/latest')
def system_alpha_validation_decisions_latest(limit: int = 20) -> dict:
    return _alpha_validation.alpha_validation_decisions_latest(limit=limit)


@router.get('/system/alpha-validation-failures/latest')
def system_alpha_validation_failures_latest(limit: int = 20) -> dict:
    return _alpha_validation.alpha_validation_failures_latest(limit=limit)


@router.post('/system/alpha-ensemble/run')
def system_alpha_ensemble_run(limit: int = 20) -> dict:
    return _alpha_ensemble.run(limit=limit)


@router.get('/system/alpha-ensemble/latest')
def system_alpha_ensemble_latest(limit: int = 20) -> dict:
    return _alpha_ensemble.latest(limit=limit)


@router.get('/system/alpha-ensemble/candidates/latest')
def system_alpha_ensemble_candidates_latest(limit: int = 20) -> dict:
    return _alpha_ensemble.alpha_ensemble_candidates_latest(limit=limit)


@router.get('/system/alpha-ensemble/candidate/{ensemble_id}')
def system_alpha_ensemble_candidate(ensemble_id: str) -> dict:
    return _alpha_ensemble.alpha_ensemble_candidate(ensemble_id)


@router.get('/system/alpha-ensemble-correlation/latest')
def system_alpha_ensemble_correlation_latest(limit: int = 20) -> dict:
    return _alpha_ensemble.alpha_ensemble_correlation_latest(limit=limit)


@router.get('/system/alpha-marginal-contribution/latest')
def system_alpha_marginal_contribution_latest(limit: int = 20) -> dict:
    return _alpha_ensemble.alpha_marginal_contribution_latest(limit=limit)


@router.get('/system/alpha-ensemble-selection/latest')
def system_alpha_ensemble_selection_latest(limit: int = 20) -> dict:
    return _alpha_ensemble.alpha_ensemble_selection_latest(limit=limit)


@router.get('/system/alpha-ensemble-weights/latest')
def system_alpha_ensemble_weights_latest(limit: int = 20) -> dict:
    return _alpha_ensemble.alpha_ensemble_weights_latest(limit=limit)


@router.post('/system/alpha-factor-attribution/run')
def system_alpha_factor_attribution_run(limit: int = 20) -> dict:
    return _alpha_attribution.run(limit=limit)


@router.get('/system/alpha-factor-attribution/latest')
def system_alpha_factor_attribution_latest(limit: int = 20) -> dict:
    return _alpha_attribution.latest(limit=limit)


@router.get('/system/alpha-factor-attribution/candidate/{alpha_id}')
def system_alpha_factor_attribution_candidate(alpha_id: str) -> dict:
    return _alpha_attribution.alpha_factor_attribution_candidate(alpha_id)


@router.get('/system/alpha-factor-exposure/latest')
def system_alpha_factor_exposure_latest(limit: int = 20) -> dict:
    return _alpha_attribution.alpha_factor_exposure_latest(limit=limit)


@router.get('/system/alpha-residual-alpha/latest')
def system_alpha_residual_alpha_latest(limit: int = 20) -> dict:
    return _alpha_attribution.alpha_residual_alpha_latest(limit=limit)


@router.get('/system/alpha-economic-risk/latest')
def system_alpha_economic_risk_latest(limit: int = 20) -> dict:
    return _alpha_attribution.alpha_economic_risk_latest(limit=limit)


@router.get('/system/alpha-factor-concentration/latest')
def system_alpha_factor_concentration_latest(limit: int = 20) -> dict:
    return _alpha_attribution.alpha_factor_concentration_latest(limit=limit)


@router.get('/system/alpha-economic-meaning/latest')
def system_alpha_economic_meaning_latest(limit: int = 20) -> dict:
    return _alpha_attribution.alpha_economic_meaning_latest(limit=limit)


@router.get('/system/alpha-factor-attribution/ensemble/{ensemble_id}')
def system_alpha_factor_attribution_ensemble(ensemble_id: str) -> dict:
    return _alpha_attribution.alpha_factor_attribution_ensemble(ensemble_id)


@router.post('/system/alpha-capacity/run')
def system_alpha_capacity_run(limit: int = 20) -> dict:
    return _alpha_capacity.run(limit=limit)


@router.get('/system/alpha-capacity/latest')
def system_alpha_capacity_latest(limit: int = 20) -> dict:
    return _alpha_capacity.latest(limit=limit)


@router.get('/system/alpha-capacity/candidate/{alpha_id}')
def system_alpha_capacity_candidate(alpha_id: str) -> dict:
    return _alpha_capacity.alpha_capacity_candidate(alpha_id)


@router.get('/system/alpha-crowding/latest')
def system_alpha_crowding_latest(limit: int = 20) -> dict:
    return _alpha_capacity.alpha_crowding_latest(limit=limit)


@router.get('/system/alpha-impact/latest')
def system_alpha_impact_latest(limit: int = 20) -> dict:
    return _alpha_capacity.alpha_impact_latest(limit=limit)


@router.get('/system/alpha-capacity/ensemble/{ensemble_id}')
def system_alpha_capacity_ensemble(ensemble_id: str) -> dict:
    return _alpha_capacity.alpha_capacity_ensemble(ensemble_id)


@router.post('/system/alpha-dynamic-weights/run')
def system_alpha_dynamic_weights_run(limit: int = 20) -> dict:
    return _alpha_weighting.run(limit=limit)


@router.get('/system/alpha-dynamic-weights/latest')
def system_alpha_dynamic_weights_latest(limit: int = 20) -> dict:
    return _alpha_weighting.latest(limit=limit)


@router.get('/system/alpha-dynamic-weights/ensemble/{ensemble_id}')
def system_alpha_dynamic_weights_ensemble(ensemble_id: str) -> dict:
    return _alpha_weighting.alpha_dynamic_weights_ensemble(ensemble_id)


@router.get('/system/alpha-weight-adjustments/latest')
def system_alpha_weight_adjustments_latest(limit: int = 20) -> dict:
    return _alpha_weighting.alpha_weight_adjustments_latest(limit=limit)


@router.get('/system/alpha-weight-drift/latest')
def system_alpha_weight_drift_latest(limit: int = 20) -> dict:
    return _alpha_weighting.alpha_weight_drift_latest(limit=limit)


@router.get('/system/alpha-weight-constraints/latest')
def system_alpha_weight_constraints_latest(limit: int = 20) -> dict:
    return _alpha_weighting.alpha_weight_constraints_latest(limit=limit)


@router.get('/system/alpha-weight-proposals/latest')
def system_alpha_weight_proposals_latest(limit: int = 20) -> dict:
    return _alpha_weighting.alpha_weight_proposals_latest(limit=limit)


@router.post('/system/alpha-kill-switch/run')
def system_alpha_kill_switch_run(limit: int = 20) -> dict:
    return _alpha_retirement.run(limit=limit)


@router.get('/system/alpha-kill-switch/latest')
def system_alpha_kill_switch_latest(limit: int = 20) -> dict:
    return _alpha_retirement.latest(limit=limit)


@router.get('/system/alpha-kill-switch/alpha/{alpha_id}')
def system_alpha_kill_switch_alpha(alpha_id: str) -> dict:
    return _alpha_retirement.alpha_kill_switch_alpha(alpha_id)


@router.get('/system/alpha-retirement/latest')
def system_alpha_retirement_latest(limit: int = 20) -> dict:
    return _alpha_retirement.alpha_retirement_latest(limit=limit)


@router.get('/system/alpha-retirement/alpha/{alpha_id}')
def system_alpha_retirement_alpha(alpha_id: str) -> dict:
    return _alpha_retirement.alpha_retirement_alpha(alpha_id)


@router.get('/system/alpha-deactivation-decisions/latest')
def system_alpha_deactivation_decisions_latest(limit: int = 20) -> dict:
    return _alpha_retirement.alpha_deactivation_decisions_latest(limit=limit)


@router.get('/system/alpha-kill-switch-events/latest')
def system_alpha_kill_switch_events_latest(limit: int = 20) -> dict:
    return _alpha_retirement.alpha_kill_switch_events_latest(limit=limit)


@router.post('/system/alpha-kill-switch/override')
def system_alpha_kill_switch_override(alpha_id: str = "manual.override", action: str = "continue", reason: str = "operator_override") -> dict:
    return _alpha_retirement.override(alpha_id=alpha_id, action=action, reason=reason)


@router.post('/system/alpha-feedback-loop/run')
def system_alpha_feedback_loop_run(limit: int = 20) -> dict:
    return _alpha_feedback.run(limit=limit)


@router.get('/system/alpha-feedback-loop/latest')
def system_alpha_feedback_loop_latest(limit: int = 20) -> dict:
    return _alpha_feedback.latest(limit=limit)


@router.get('/system/alpha-learning-signals/latest')
def system_alpha_learning_signals_latest(limit: int = 20) -> dict:
    return _alpha_feedback.alpha_learning_signals_latest(limit=limit)


@router.get('/system/alpha-generation-priors/latest')
def system_alpha_generation_priors_latest(limit: int = 20) -> dict:
    return _alpha_feedback.alpha_generation_priors_latest(limit=limit)


@router.get('/system/alpha-family-performance/latest')
def system_alpha_family_performance_latest(limit: int = 20) -> dict:
    return _alpha_feedback.alpha_family_performance_latest(limit=limit)


@router.get('/system/alpha-policy-recommendations/latest')
def system_alpha_policy_recommendations_latest(limit: int = 20) -> dict:
    return _alpha_feedback.alpha_policy_recommendations_latest(limit=limit)


@router.get('/system/alpha-feedback-loop/alpha/{alpha_id}')
def system_alpha_feedback_loop_alpha(alpha_id: str) -> dict:
    return _alpha_feedback.alpha_feedback_loop_alpha(alpha_id)


@router.get('/system/alpha-feedback-loop/family/{family_id}')
def system_alpha_feedback_loop_family(family_id: str) -> dict:
    return _alpha_feedback.alpha_feedback_loop_family(family_id)


@router.post('/system/alpha-policy-recommendations/apply')
def system_alpha_policy_recommendations_apply(recommendation_id: str = "latest", approval: str = "operator_approved") -> dict:
    return _alpha_feedback.apply_policy_recommendations(recommendation_id=recommendation_id, approval=approval)


@router.post('/system/operational-risk/run')
def system_operational_risk_run(limit: int = 20) -> dict:
    return _operational_risk.run(limit=limit)


@router.get('/system/risk-state/latest')
def system_risk_state_latest() -> dict:
    return _operational_risk.risk_state_latest()


@router.get('/system/global-risk-metrics/latest')
def system_global_risk_metrics_latest(limit: int = 20) -> dict:
    return _operational_risk.global_risk_metrics_latest(limit=limit)


@router.get('/system/anomaly-detection/latest')
def system_anomaly_detection_latest(limit: int = 20) -> dict:
    return _operational_risk.anomaly_detection_latest(limit=limit)


@router.get('/system/operational-incidents/latest')
def system_operational_incidents_latest(limit: int = 20) -> dict:
    return _operational_risk.operational_incidents_latest(limit=limit)


@router.get('/system/risk-response/latest')
def system_risk_response_latest(limit: int = 20) -> dict:
    return _operational_risk.risk_response_latest(limit=limit)


@router.post('/system/risk-response/execute')
def system_risk_response_execute(action_id: str = "latest", approved: bool = False) -> dict:
    return _operational_risk.execute_response(action_id=action_id, approved=approved)


@router.post('/system/global-kill-switch')
def system_global_kill_switch(
    trigger_reason: str = "operator_requested",
    risk_level: str = "L5_GLOBAL_HALT",
    kill_scope: str = "global",
    operator_id: str = "operator",
) -> dict:
    return _operational_risk.trigger_global_kill(
        trigger_reason=trigger_reason,
        risk_level=risk_level,
        kill_scope=kill_scope,
        operator_id=operator_id,
    )


@router.get('/system/global-kill-switch/latest')
def system_global_kill_switch_latest(limit: int = 20) -> dict:
    return _operational_risk.global_kill_switch_latest(limit=limit)


@router.post('/system/operational-risk/override')
def system_operational_risk_override(
    operator_id: str = "operator",
    override_scope: str = "system",
    override_reason: str = "manual_override",
) -> dict:
    return _operational_risk.override(
        operator_id=operator_id,
        override_scope=override_scope,
        override_reason=override_reason,
    )


@router.post('/system/risk-response/orchestrate')
def system_risk_response_orchestrate() -> dict:
    return _operational_risk.orchestrate_response()


@router.get('/system/risk-response-orchestration/latest')
def system_risk_response_orchestration_latest(limit: int = 20) -> dict:
    return _operational_risk.risk_response_orchestration_latest(limit=limit)


@router.get('/system/runtime-safe-mode/latest')
def system_runtime_safe_mode_latest(limit: int = 20) -> dict:
    return _operational_risk.runtime_safe_mode_latest(limit=limit)


@router.get('/system/order-permission-matrix/latest')
def system_order_permission_matrix_latest() -> dict:
    return _operational_risk.order_permission_matrix_latest()


@router.get('/system/risk-recovery-readiness/latest')
def system_risk_recovery_readiness_latest(limit: int = 20) -> dict:
    return _operational_risk.recovery_readiness_latest(limit=limit)


@router.post('/system/risk-recovery/request')
def system_risk_recovery_request(operator_id: str = "operator", reason: str = "operator_recovery_request") -> dict:
    return _operational_risk.request_risk_recovery(operator_id=operator_id, reason=reason)


@router.post('/system/execution-health/run')
def system_execution_health_run(limit: int = 20) -> dict:
    return _execution_health.run(limit=limit)


@router.get('/system/execution-health/latest')
def system_execution_health_latest(limit: int = 20) -> dict:
    return _execution_health.latest(limit=limit)


@router.get('/system/broker-health/latest')
def system_broker_health_latest(limit: int = 20) -> dict:
    return _execution_health.broker_health_latest(limit=limit)


@router.get('/system/venue-health/latest')
def system_venue_health_latest(limit: int = 20) -> dict:
    return _execution_health.venue_health_latest(limit=limit)


@router.get('/system/execution-anomalies/latest')
def system_execution_anomalies_latest(limit: int = 20) -> dict:
    return _execution_health.execution_anomalies_latest(limit=limit)


@router.get('/system/execution-incidents/latest')
def system_execution_incidents_latest(limit: int = 20) -> dict:
    return _execution_health.execution_incidents_latest(limit=limit)


@router.get('/system/execution-safe-mode-recommendation/latest')
def system_execution_safe_mode_recommendation_latest(limit: int = 20) -> dict:
    return _execution_health.execution_safe_mode_recommendation_latest(limit=limit)


@router.get('/system/broker-health/{broker_id}')
def system_broker_health(broker_id: str) -> dict:
    return _execution_health.broker_health(broker_id)


@router.get('/system/venue-health/{venue_id}')
def system_venue_health(venue_id: str) -> dict:
    return _execution_health.venue_health(venue_id)


@router.post('/system/data-integrity/run')
def system_data_integrity_run(limit: int = 20) -> dict:
    return _data_integrity.run(limit=limit)


@router.get('/system/data-integrity/latest')
def system_data_integrity_latest(limit: int = 20) -> dict:
    return _data_integrity.latest(limit=limit)


@router.get('/system/market-feed-health/latest')
def system_market_feed_health_latest(limit: int = 20) -> dict:
    return _data_integrity.market_feed_health_latest(limit=limit)


@router.get('/system/market-feed-health/{feed_id}')
def system_market_feed_health(feed_id: str) -> dict:
    return _data_integrity.market_feed_health(feed_id)


@router.get('/system/symbol-data-health/latest')
def system_symbol_data_health_latest(limit: int = 20) -> dict:
    return _data_integrity.symbol_data_health_latest(limit=limit)


@router.get('/system/symbol-data-health/{symbol}')
def system_symbol_data_health(symbol: str) -> dict:
    return _data_integrity.symbol_data_health(symbol)


@router.get('/system/data-anomalies/latest')
def system_data_anomalies_latest(limit: int = 20) -> dict:
    return _data_integrity.data_anomalies_latest(limit=limit)


@router.get('/system/data-incidents/latest')
def system_data_incidents_latest(limit: int = 20) -> dict:
    return _data_integrity.data_incidents_latest(limit=limit)


@router.get('/system/mark-reliability/latest')
def system_mark_reliability_latest(limit: int = 20) -> dict:
    return _data_integrity.mark_reliability_latest(limit=limit)


@router.get('/system/data-safe-mode-recommendation/latest')
def system_data_safe_mode_recommendation_latest(limit: int = 20) -> dict:
    return _data_integrity.data_safe_mode_recommendation_latest(limit=limit)


@router.post('/system/orc-governance/sync')
def system_orc_governance_sync(limit: int = 20) -> dict:
    return _operational_governance.sync(limit=limit)


@router.get('/system/orc-governance/latest')
def system_orc_governance_latest(limit: int = 20) -> dict:
    return _operational_governance.latest(limit=limit)


@router.get('/system/orc-governance/incidents/latest')
def system_orc_governance_incidents_latest(limit: int = 20) -> dict:
    return _operational_governance.incidents_latest(limit=limit)


@router.get('/system/orc-governance/incident/{incident_id}')
def system_orc_governance_incident(incident_id: str) -> dict:
    return _operational_governance.incident(incident_id=incident_id)


@router.get('/system/orc-governance/pending-approvals/latest')
def system_orc_governance_pending_approvals_latest(limit: int = 20) -> dict:
    return _operational_governance.pending_approvals_latest(limit=limit)


@router.get('/system/orc-governance/audit/latest')
def system_orc_governance_audit_latest(limit: int = 20) -> dict:
    return _operational_governance.audit_latest(limit=limit)


@router.post('/system/orc-governance/recovery/request')
def system_orc_governance_recovery_request(
    source_incident_id: str = "latest",
    requested_target_level: str = "L1_WATCH",
    operator_id: str = "operator",
) -> dict:
    return _operational_governance.request_recovery(
        source_incident_id=source_incident_id,
        requested_target_level=requested_target_level,
        operator_id=operator_id,
    )


@router.get('/system/orc-governance/recovery/latest')
def system_orc_governance_recovery_latest(limit: int = 20) -> dict:
    return _operational_governance.recovery_latest(limit=limit)
