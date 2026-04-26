from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import json
from typing import Any

from ai_hedge_bot.core.clock import utc_now_iso
from ai_hedge_bot.core.ids import new_run_id


class HealthComponent(str, Enum):
    EXECUTION = "EXECUTION"
    DATA_FEED = "DATA_FEED"
    ALPHA = "ALPHA"
    RISK = "RISK"
    INFRA = "INFRA"
    GOVERNANCE = "GOVERNANCE"


class HealthSignalType(str, Enum):
    LATENCY_MS = "latency_ms"
    ERROR_RATE = "error_rate"
    DATA_FRESHNESS_SEC = "data_freshness_sec"
    QUEUE_LAG = "queue_lag"
    EXECUTION_FAILURE_RATE = "execution_failure_rate"
    HEARTBEAT_AGE_SEC = "heartbeat_age_sec"


class SeverityLevel(str, Enum):
    S0 = "S0_HEALTHY"
    S1 = "S1_MINOR_DEGRADATION"
    S2 = "S2_MODERATE_DEGRADATION"
    S3 = "S3_MAJOR_DEGRADATION_SAFE_MODE"
    S4 = "S4_CRITICAL_HALT"


class ControlActionType(str, Enum):
    LOG_ONLY = "LOG_ONLY"
    WARN = "WARN"
    PARTIAL_THROTTLE = "PARTIAL_THROTTLE"
    SAFE_MODE = "SAFE_MODE"
    HALT = "HALT"
    RECOVERY = "RECOVERY"


@dataclass(frozen=True)
class HealthSignal:
    component: HealthComponent
    signal_type: HealthSignalType
    value: float
    source: str
    observed_at: str = field(default_factory=utc_now_iso)
    metadata: dict[str, Any] = field(default_factory=dict)
    signal_id: str = field(default_factory=lambda: new_run_id().replace("run_", "health_signal_", 1))

    def to_row(self) -> dict[str, Any]:
        return {
            "signal_id": self.signal_id,
            "component": self.component.value,
            "signal_type": self.signal_type.value,
            "value": self.value,
            "source": self.source,
            "observed_at": self.observed_at,
            "metadata_json": stable_json(self.metadata),
        }


@dataclass(frozen=True)
class ComponentHealthScore:
    component: HealthComponent
    score: float
    severity: SeverityLevel
    signals: list[HealthSignal]
    reason: str
    evaluated_at: str = field(default_factory=utc_now_iso)
    score_id: str = field(default_factory=lambda: new_run_id().replace("run_", "health_score_", 1))

    def to_row(self, snapshot_id: str) -> dict[str, Any]:
        return {
            "score_id": self.score_id,
            "snapshot_id": snapshot_id,
            "component": self.component.value,
            "score": self.score,
            "severity": self.severity.value,
            "reason": self.reason,
            "evaluated_at": self.evaluated_at,
            "signal_ids_json": stable_json([signal.signal_id for signal in self.signals]),
        }


@dataclass(frozen=True)
class SystemHealthSnapshot:
    snapshot_id: str
    system_score: float
    severity: SeverityLevel
    components: list[ComponentHealthScore]
    created_at: str = field(default_factory=utc_now_iso)

    def to_row(self) -> dict[str, Any]:
        return {
            "snapshot_id": self.snapshot_id,
            "system_score": self.system_score,
            "severity": self.severity.value,
            "created_at": self.created_at,
            "components_json": stable_json(
                [
                    {
                        "component": score.component.value,
                        "score": score.score,
                        "severity": score.severity.value,
                        "reason": score.reason,
                        "signal_ids": [signal.signal_id for signal in score.signals],
                    }
                    for score in self.components
                ]
            ),
        }


@dataclass(frozen=True)
class DegradationEvent:
    event_id: str
    snapshot_id: str
    component: HealthComponent | None
    severity: SeverityLevel
    reason: str
    detected_at: str = field(default_factory=utc_now_iso)
    is_active: bool = True

    def to_row(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "snapshot_id": self.snapshot_id,
            "component": self.component.value if self.component else "",
            "severity": self.severity.value,
            "reason": self.reason,
            "detected_at": self.detected_at,
            "is_active": self.is_active,
        }


@dataclass(frozen=True)
class ControlAction:
    action_id: str
    degradation_event_id: str
    action_type: ControlActionType
    severity: SeverityLevel
    target_component: HealthComponent | None
    payload: dict[str, Any]
    requires_governance_audit: bool = True
    executed_at: str = field(default_factory=utc_now_iso)

    def to_row(self) -> dict[str, Any]:
        return {
            "action_id": self.action_id,
            "degradation_event_id": self.degradation_event_id,
            "action_type": self.action_type.value,
            "severity": self.severity.value,
            "target_component": self.target_component.value if self.target_component else "",
            "payload_json": stable_json(self.payload),
            "requires_governance_audit": self.requires_governance_audit,
            "executed_at": self.executed_at,
        }


@dataclass(frozen=True)
class RecoveryAttempt:
    recovery_id: str
    degradation_event_id: str
    strategy: str
    status: str
    detail: str
    created_at: str = field(default_factory=utc_now_iso)

    def to_row(self) -> dict[str, Any]:
        return {
            "recovery_id": self.recovery_id,
            "degradation_event_id": self.degradation_event_id,
            "strategy": self.strategy,
            "status": self.status,
            "detail": self.detail,
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


def component_from(value: str) -> HealthComponent:
    raw = str(value or "INFRA").upper()
    aliases = {"DATAFEED": "DATA_FEED", "DATA": "DATA_FEED"}
    return HealthComponent(aliases.get(raw, raw))


def signal_type_from(value: str) -> HealthSignalType:
    return HealthSignalType(str(value or HealthSignalType.HEARTBEAT_AGE_SEC.value).lower())

