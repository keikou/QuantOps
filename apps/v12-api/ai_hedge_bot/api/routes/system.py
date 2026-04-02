from __future__ import annotations

from fastapi import APIRouter
from ai_hedge_bot.app.container import CONTAINER
from ai_hedge_bot.services.hardening_architect_handoff_service import HardeningArchitectHandoffService
from ai_hedge_bot.services.hardening_evidence_snapshot_service import HardeningEvidenceSnapshotService
from ai_hedge_bot.services.hardening_handover_manifest_service import HardeningHandoverManifestService
from ai_hedge_bot.services.hardening_status_service import HardeningStatusService
from ai_hedge_bot.services.operator_diagnostic_bundle_service import OperatorDiagnosticBundleService
from ai_hedge_bot.services.recovery_replay_diagnostic_bundle_service import RecoveryReplayDiagnosticBundleService
from ai_hedge_bot.services.resume_operator_packet_service import ResumeOperatorPacketService

router = APIRouter(tags=['system'])
_hardening_architect_handoff = HardeningArchitectHandoffService()
_hardening_snapshot = HardeningEvidenceSnapshotService()
_hardening_manifest = HardeningHandoverManifestService()
_hardening_status = HardeningStatusService()
_operator_bundle = OperatorDiagnosticBundleService()
_recovery_replay_bundle = RecoveryReplayDiagnosticBundleService()
_resume_operator_packet = ResumeOperatorPacketService()


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
