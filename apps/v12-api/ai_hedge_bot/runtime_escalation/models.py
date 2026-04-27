from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import json
from typing import Any

from ai_hedge_bot.core.clock import utc_now_iso
from ai_hedge_bot.core.ids import new_run_id


class SourceType(str, Enum):
    RUNTIME_DEGRADATION = "RUNTIME_DEGRADATION"
    SAFE_MODE_TRIGGERED = "SAFE_MODE_TRIGGERED"
    SYSTEM_HALTED = "SYSTEM_HALTED"
    DEPENDENCY_OUTAGE = "DEPENDENCY_OUTAGE"
    CIRCUIT_OPEN_CRITICAL = "CIRCUIT_OPEN_CRITICAL"
    FALLBACK_UNAVAILABLE = "FALLBACK_UNAVAILABLE"
    RECOVERY_PROBE_FAILED = "RECOVERY_PROBE_FAILED"


class EscalationLevel(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"
    EMERGENCY = "EMERGENCY"


class NotificationStatus(str, Enum):
    CREATED = "CREATED"
    DELIVERED = "DELIVERED"
    ACK_REQUIRED = "ACK_REQUIRED"
    ACKED = "ACKED"
    ESCALATED = "ESCALATED"
    RESOLVED = "RESOLVED"
    EXPIRED = "EXPIRED"


class AuditEventType(str, Enum):
    RULE_EVALUATED = "RULE_EVALUATED"
    ESCALATION_CREATED = "ESCALATION_CREATED"
    NOTIFICATION_CREATED = "NOTIFICATION_CREATED"
    DUPLICATE_SUPPRESSED = "DUPLICATE_SUPPRESSED"
    ACK_RECEIVED = "ACK_RECEIVED"
    ACK_EXPIRED = "ACK_EXPIRED"
    HANDOFF_CREATED = "HANDOFF_CREATED"
    HANDOFF_FAILED = "HANDOFF_FAILED"
    HANDOFF_INGESTED = "HANDOFF_INGESTED"


@dataclass(frozen=True)
class EscalationRule:
    rule_id: str
    source_type: SourceType
    source_severity_min: str
    target_escalation_level: EscalationLevel
    notification_channel: str = "OPERATOR_QUEUE"
    requires_ack: bool = True
    handoff_to_afg04: bool = True
    cooldown_seconds: int = 900
    dedup_key_template: str = "{source_type}:{component}:{dependency_id}:{severity}"
    enabled: bool = True
    created_at: str = field(default_factory=utc_now_iso)

    def to_row(self) -> dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "source_type": self.source_type.value,
            "source_severity_min": self.source_severity_min,
            "target_escalation_level": self.target_escalation_level.value,
            "notification_channel": self.notification_channel,
            "requires_ack": self.requires_ack,
            "handoff_to_afg04": self.handoff_to_afg04,
            "cooldown_seconds": self.cooldown_seconds,
            "dedup_key_template": self.dedup_key_template,
            "enabled": self.enabled,
            "created_at": self.created_at,
        }


def stable_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)


def parse_json(value: Any, default: Any = None) -> Any:
    if value in (None, ""):
        return default
    if isinstance(value, (dict, list)):
        return value
    try:
        return json.loads(str(value))
    except Exception:
        return default


def normalize_severity(value: Any) -> str:
    raw = str(value or "S3").upper()
    if raw.startswith("S4"):
        return "S4"
    if raw.startswith("S3"):
        return "S3"
    if raw.startswith("S2"):
        return "S2"
    if raw.startswith("S1"):
        return "S1"
    return raw


def severity_rank(value: Any) -> int:
    return {"S0": 0, "S1": 1, "S2": 2, "S3": 3, "S4": 4}.get(normalize_severity(value), 3)


def utc_plus_seconds_iso(seconds: int) -> str:
    from datetime import datetime, timedelta, timezone

    return (datetime.now(timezone.utc) + timedelta(seconds=max(int(seconds), 0))).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def new_id(prefix: str) -> str:
    return new_run_id().replace("run_", prefix, 1)
