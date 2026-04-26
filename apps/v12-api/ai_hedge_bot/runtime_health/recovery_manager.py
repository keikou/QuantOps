from __future__ import annotations

from ai_hedge_bot.core.ids import new_run_id
from ai_hedge_bot.runtime_health.models import DegradationEvent, RecoveryAttempt, SeverityLevel


class RecoveryManager:
    def create_recovery_attempt(self, event: DegradationEvent) -> RecoveryAttempt:
        if event.severity == SeverityLevel.S1:
            strategy = "observe_only"
            status = "not_required"
        elif event.severity == SeverityLevel.S2:
            strategy = "retry_and_throttle"
            status = "scheduled"
        elif event.severity == SeverityLevel.S3:
            strategy = "safe_mode_then_recover"
            status = "scheduled"
        else:
            strategy = "halt_and_operator_escalation"
            status = "operator_required"
        return RecoveryAttempt(
            recovery_id=new_run_id().replace("run_", "runtime_recovery_", 1),
            degradation_event_id=event.event_id,
            strategy=strategy,
            status=status,
            detail=f"Recovery strategy selected for {event.severity.value}",
        )

