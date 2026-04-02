from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from ai_hedge_bot.app.container import CONTAINER
from ai_hedge_bot.services.hardening_status_service import HardeningStatusService
from ai_hedge_bot.services.operator_diagnostic_bundle_service import OperatorDiagnosticBundleService
from ai_hedge_bot.services.recovery_replay_diagnostic_bundle_service import RecoveryReplayDiagnosticBundleService


class HardeningEvidenceSnapshotService:
    SNAPSHOT_NAME = "hardening_evidence_latest"

    def __init__(self) -> None:
        self.hardening_status = HardeningStatusService()
        self.operator_bundle = OperatorDiagnosticBundleService()
        self.recovery_bundle = RecoveryReplayDiagnosticBundleService()

    def build_payload(self) -> dict[str, Any]:
        generated_at = datetime.now(timezone.utc).isoformat()
        hardening_status = self.hardening_status.build()
        operator_bundle = self.operator_bundle.build()
        recovery_bundle = self.recovery_bundle.build()
        payload = {
            "status": "ok",
            "track": "System Reliability Hardening Track",
            "branch_expectation": "codex/post-phase7-hardening",
            "generated_at": generated_at,
            "hardening_status": hardening_status,
            "operator_diagnostic_bundle": operator_bundle,
            "recovery_replay_diagnostic_bundle": recovery_bundle,
        }
        return json.loads(json.dumps(payload, ensure_ascii=False, default=str))

    def save(self) -> dict[str, Any]:
        payload = self.build_payload()
        path = CONTAINER.snapshot_service.save(self.SNAPSHOT_NAME, payload)
        return {
            "status": "ok",
            "path": path,
            "snapshot": payload,
        }

    def load(self) -> dict[str, Any]:
        payload = CONTAINER.snapshot_service.load(self.SNAPSHOT_NAME)
        if payload.get("status") == "missing":
            return payload
        return {
            "status": "ok",
            "snapshot": payload,
        }
