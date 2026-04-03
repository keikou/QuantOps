from __future__ import annotations

from fastapi import APIRouter
from ai_hedge_bot.app.container import CONTAINER
from ai_hedge_bot.services.hardening_architect_handoff_service import HardeningArchitectHandoffService
from ai_hedge_bot.services.hardening_evidence_snapshot_service import HardeningEvidenceSnapshotService
from ai_hedge_bot.services.hardening_handover_manifest_service import HardeningHandoverManifestService
from ai_hedge_bot.services.hardening_status_service import HardeningStatusService
from ai_hedge_bot.services.operator_diagnostic_bundle_service import OperatorDiagnosticBundleService
from ai_hedge_bot.services.policy_optimization_meta_control_learning_service import (
    PolicyOptimizationMetaControlLearningService,
)
from ai_hedge_bot.services.recovery_replay_diagnostic_bundle_service import RecoveryReplayDiagnosticBundleService
from ai_hedge_bot.services.resume_operator_packet_service import ResumeOperatorPacketService
from ai_hedge_bot.services.system_level_learning_feedback_integration_service import (
    SystemLevelLearningFeedbackIntegrationService,
)

router = APIRouter(tags=['system'])
_hardening_architect_handoff = HardeningArchitectHandoffService()
_hardening_snapshot = HardeningEvidenceSnapshotService()
_hardening_manifest = HardeningHandoverManifestService()
_hardening_status = HardeningStatusService()
_operator_bundle = OperatorDiagnosticBundleService()
_policy_optimization = PolicyOptimizationMetaControlLearningService()
_recovery_replay_bundle = RecoveryReplayDiagnosticBundleService()
_resume_operator_packet = ResumeOperatorPacketService()
_system_learning_feedback = SystemLevelLearningFeedbackIntegrationService()


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
