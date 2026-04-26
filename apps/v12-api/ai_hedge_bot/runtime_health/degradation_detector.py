from __future__ import annotations

from ai_hedge_bot.core.ids import new_run_id
from ai_hedge_bot.runtime_health.models import DegradationEvent, SeverityLevel, SystemHealthSnapshot


class DegradationDetector:
    DEGRADED = {SeverityLevel.S1, SeverityLevel.S2, SeverityLevel.S3, SeverityLevel.S4}

    def detect(self, snapshot: SystemHealthSnapshot) -> list[DegradationEvent]:
        events: list[DegradationEvent] = []
        for component_score in snapshot.components:
            if component_score.severity in self.DEGRADED:
                events.append(
                    DegradationEvent(
                        event_id=new_run_id().replace("run_", "degradation_", 1),
                        snapshot_id=snapshot.snapshot_id,
                        component=component_score.component,
                        severity=component_score.severity,
                        reason=component_score.reason,
                    )
                )
        if snapshot.severity in {SeverityLevel.S3, SeverityLevel.S4}:
            events.append(
                DegradationEvent(
                    event_id=new_run_id().replace("run_", "degradation_", 1),
                    snapshot_id=snapshot.snapshot_id,
                    component=None,
                    severity=snapshot.severity,
                    reason=f"system severity={snapshot.severity.value} score={snapshot.system_score:.4f}",
                )
            )
        return events

