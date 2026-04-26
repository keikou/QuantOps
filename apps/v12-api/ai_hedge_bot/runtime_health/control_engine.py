from __future__ import annotations

from ai_hedge_bot.core.ids import new_run_id
from ai_hedge_bot.runtime_health.models import ControlAction, ControlActionType, DegradationEvent, SeverityLevel


class RuntimeControlEngine:
    def action_for_event(self, event: DegradationEvent) -> ControlAction:
        if event.severity == SeverityLevel.S1:
            action_type = ControlActionType.LOG_ONLY
            payload = {"notify": False, "throttle": 0.0}
        elif event.severity == SeverityLevel.S2:
            action_type = ControlActionType.PARTIAL_THROTTLE
            payload = {"notify": True, "throttle": 0.25}
        elif event.severity == SeverityLevel.S3:
            action_type = ControlActionType.SAFE_MODE
            payload = {"notify": True, "safe_mode": True, "capital_multiplier": 0.25}
        else:
            action_type = ControlActionType.HALT
            payload = {"notify": True, "halt": True, "capital_multiplier": 0.0}
        return ControlAction(
            action_id=new_run_id().replace("run_", "runtime_control_", 1),
            degradation_event_id=event.event_id,
            action_type=action_type,
            severity=event.severity,
            target_component=event.component,
            payload=payload,
        )

    def safe_mode_action(self, reason: str = "operator_requested") -> ControlAction:
        event = DegradationEvent(
            event_id=new_run_id().replace("run_", "degradation_", 1),
            snapshot_id="manual",
            component=None,
            severity=SeverityLevel.S3,
            reason=reason,
        )
        return self.action_for_event(event)

