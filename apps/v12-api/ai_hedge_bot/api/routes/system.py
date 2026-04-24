from __future__ import annotations

from fastapi import APIRouter
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
