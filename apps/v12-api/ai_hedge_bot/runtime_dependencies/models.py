from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import json
from typing import Any

from ai_hedge_bot.core.clock import utc_now_iso
from ai_hedge_bot.core.ids import new_run_id


class DependencyType(str, Enum):
    DATA_FEED = "DATA_FEED"
    EXECUTION_VENUE = "EXECUTION_VENUE"
    BROKER_ADAPTER = "BROKER_ADAPTER"
    MODEL_SERVICE = "MODEL_SERVICE"
    STORAGE = "STORAGE"
    QUEUE = "QUEUE"
    SCHEDULER = "SCHEDULER"
    INTERNAL_API = "INTERNAL_API"
    EXTERNAL_API = "EXTERNAL_API"


class CircuitState(str, Enum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"


class DependencyHealthStatus(str, Enum):
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"


class DependencyEventType(str, Enum):
    FAILURE_DETECTED = "FAILURE_DETECTED"
    CIRCUIT_OPENED = "CIRCUIT_OPENED"
    FALLBACK_SELECTED = "FALLBACK_SELECTED"
    ISOLATED = "ISOLATED"
    RECOVERY_PROBE_SCHEDULED = "RECOVERY_PROBE_SCHEDULED"
    RECOVERY_SUCCEEDED = "RECOVERY_SUCCEEDED"
    RECOVERY_FAILED = "RECOVERY_FAILED"


class ProbeStatus(str, Enum):
    SCHEDULED = "SCHEDULED"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


@dataclass(frozen=True)
class DependencyRegistration:
    dependency_id: str
    dependency_type: DependencyType
    name: str
    owner: str
    criticality: str = "standard"
    fallback_dependency_id: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    registered_at: str = field(default_factory=utc_now_iso)
    is_active: bool = True

    def to_row(self) -> dict[str, Any]:
        return {
            "dependency_id": self.dependency_id,
            "dependency_type": self.dependency_type.value,
            "name": self.name,
            "owner": self.owner,
            "criticality": self.criticality,
            "fallback_dependency_id": self.fallback_dependency_id,
            "metadata_json": stable_json(self.metadata),
            "registered_at": self.registered_at,
            "is_active": self.is_active,
        }


@dataclass(frozen=True)
class DependencyHealthObservation:
    dependency_id: str
    status: DependencyHealthStatus
    failure_type: str = ""
    latency_ms: float = 0.0
    detail: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    observed_at: str = field(default_factory=utc_now_iso)
    health_id: str = field(default_factory=lambda: new_run_id().replace("run_", "dep_health_", 1))

    def to_row(self) -> dict[str, Any]:
        return {
            "health_id": self.health_id,
            "dependency_id": self.dependency_id,
            "status": self.status.value,
            "failure_type": self.failure_type,
            "latency_ms": self.latency_ms,
            "observed_at": self.observed_at,
            "detail": self.detail,
            "metadata_json": stable_json(self.metadata),
        }


@dataclass(frozen=True)
class CircuitBreakerSnapshot:
    dependency_id: str
    state: CircuitState
    failure_count: int
    success_count: int
    reason: str
    threshold: int = 3
    cooldown_sec: int = 30
    metadata: dict[str, Any] = field(default_factory=dict)
    updated_at: str = field(default_factory=utc_now_iso)
    breaker_id: str = field(default_factory=lambda: new_run_id().replace("run_", "circuit_", 1))

    def to_row(self) -> dict[str, Any]:
        return {
            "breaker_id": self.breaker_id,
            "dependency_id": self.dependency_id,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "threshold": self.threshold,
            "cooldown_sec": self.cooldown_sec,
            "reason": self.reason,
            "updated_at": self.updated_at,
            "metadata_json": stable_json(self.metadata),
        }


@dataclass(frozen=True)
class CircuitTransition:
    dependency_id: str
    previous_state: CircuitState
    next_state: CircuitState
    allowed: bool
    reason: str
    created_at: str = field(default_factory=utc_now_iso)
    transition_id: str = field(default_factory=lambda: new_run_id().replace("run_", "circuit_transition_", 1))

    def to_row(self) -> dict[str, Any]:
        return {
            "transition_id": self.transition_id,
            "dependency_id": self.dependency_id,
            "previous_state": self.previous_state.value,
            "next_state": self.next_state.value,
            "allowed": self.allowed,
            "reason": self.reason,
            "created_at": self.created_at,
        }


@dataclass(frozen=True)
class DependencyEvent:
    dependency_id: str
    event_type: DependencyEventType
    circuit_state: CircuitState
    severity: str
    reason: str
    fallback_dependency_id: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=utc_now_iso)
    event_id: str = field(default_factory=lambda: new_run_id().replace("run_", "dependency_event_", 1))

    def to_row(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "dependency_id": self.dependency_id,
            "event_type": self.event_type.value,
            "circuit_state": self.circuit_state.value,
            "severity": self.severity,
            "reason": self.reason,
            "fallback_dependency_id": self.fallback_dependency_id,
            "created_at": self.created_at,
            "metadata_json": stable_json(self.metadata),
        }


@dataclass(frozen=True)
class FallbackRoute:
    dependency_id: str
    fallback_dependency_id: str
    route_status: str
    reason: str
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=utc_now_iso)
    route_id: str = field(default_factory=lambda: new_run_id().replace("run_", "fallback_route_", 1))

    def to_row(self) -> dict[str, Any]:
        return {
            "route_id": self.route_id,
            "dependency_id": self.dependency_id,
            "fallback_dependency_id": self.fallback_dependency_id,
            "route_status": self.route_status,
            "reason": self.reason,
            "created_at": self.created_at,
            "metadata_json": stable_json(self.metadata),
        }


@dataclass(frozen=True)
class RecoveryProbe:
    dependency_id: str
    circuit_state: CircuitState
    probe_status: ProbeStatus
    result_detail: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    scheduled_at: str = field(default_factory=utc_now_iso)
    completed_at: str = ""
    probe_id: str = field(default_factory=lambda: new_run_id().replace("run_", "recovery_probe_", 1))

    def to_row(self) -> dict[str, Any]:
        return {
            "probe_id": self.probe_id,
            "dependency_id": self.dependency_id,
            "circuit_state": self.circuit_state.value,
            "probe_status": self.probe_status.value,
            "scheduled_at": self.scheduled_at,
            "completed_at": self.completed_at,
            "result_detail": self.result_detail,
            "metadata_json": stable_json(self.metadata),
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


def dependency_type_from(value: str) -> DependencyType:
    raw = str(value or "INTERNAL_API").upper().replace("-", "_")
    aliases = {"DATAFEED": "DATA_FEED", "BROKER": "BROKER_ADAPTER", "API": "INTERNAL_API"}
    return DependencyType(aliases.get(raw, raw))


def circuit_state_from(value: str | None) -> CircuitState:
    return CircuitState(str(value or CircuitState.CLOSED.value).upper())
