from __future__ import annotations

from ai_hedge_bot.app.container import CONTAINER
from ai_hedge_bot.core.clock import utc_now_iso
from ai_hedge_bot.runtime_dependencies.models import (
    CircuitBreakerSnapshot,
    CircuitState,
    CircuitTransition,
    DependencyEvent,
    DependencyEventType,
    DependencyHealthObservation,
    DependencyHealthStatus,
    DependencyRegistration,
    FallbackRoute,
    ProbeStatus,
    RecoveryProbe,
    circuit_state_from,
    dependency_type_from,
    parse_json,
)


class RuntimeDependencyService:
    def __init__(self) -> None:
        self.store = CONTAINER.runtime_store

    def register_dependency(
        self,
        dependency_id: str,
        dependency_type: str = "INTERNAL_API",
        name: str = "",
        owner: str = "runtime",
        criticality: str = "standard",
        fallback_dependency_id: str = "",
        metadata_json: str = "{}",
    ) -> dict:
        registration = DependencyRegistration(
            dependency_id=dependency_id,
            dependency_type=dependency_type_from(dependency_type),
            name=name or dependency_id,
            owner=owner,
            criticality=criticality,
            fallback_dependency_id=fallback_dependency_id,
            metadata=parse_json(metadata_json, {}),
        )
        self.store.append("runtime_dependency_registry", registration.to_row())
        if not self._latest_breaker(dependency_id):
            self._append_breaker(
                dependency_id=dependency_id,
                next_state=CircuitState.CLOSED,
                previous_state=CircuitState.CLOSED,
                failure_count=0,
                success_count=0,
                reason="dependency_registered",
            )
        return {"status": "ok", "dependency": registration.to_row(), "circuit_breaker": self._latest_breaker(dependency_id)}

    def dependencies(self, limit: int = 100) -> dict:
        rows = self.store.fetchall_dict("SELECT * FROM runtime_dependency_registry ORDER BY registered_at DESC LIMIT ?", [max(int(limit), 1)])
        return {"status": "ok", "items": rows, "dependency_summary": {"dependency_count": len(rows)}}

    def dependency(self, dependency_id: str) -> dict:
        return {
            "status": "ok",
            "dependency": self._dependency_row(dependency_id),
            "health": self._latest_health(dependency_id),
            "circuit_breaker": self._latest_breaker(dependency_id),
            "fallback_route": self._latest_fallback(dependency_id),
        }

    def record_success(self, dependency_id: str, latency_ms: float = 0.0, detail: str = "dependency_success", metadata_json: str = "{}") -> dict:
        self._ensure_dependency(dependency_id)
        observation = DependencyHealthObservation(
            dependency_id=dependency_id,
            status=DependencyHealthStatus.SUCCESS,
            latency_ms=float(latency_ms),
            detail=detail,
            metadata=parse_json(metadata_json, {}),
        )
        self.store.append("runtime_dependency_health", observation.to_row())
        breaker = self._latest_breaker_or_closed(dependency_id)
        state = circuit_state_from(breaker["state"])
        result: dict = {"status": "ok", "health": observation.to_row()}
        if state == CircuitState.HALF_OPEN:
            result["circuit_breaker"] = self._append_breaker(dependency_id, CircuitState.CLOSED, state, 0, int(breaker.get("success_count") or 0) + 1, "half_open_probe_success")
            result["event"] = self._append_event(dependency_id, DependencyEventType.RECOVERY_SUCCEEDED, CircuitState.CLOSED, "S0", "recovery_probe_success")
        else:
            result["circuit_breaker"] = self._append_breaker(dependency_id, state, state, 0, int(breaker.get("success_count") or 0) + 1, "dependency_success")
        return result

    def record_failure(
        self,
        dependency_id: str,
        failure_type: str = "timeout",
        latency_ms: float = 0.0,
        detail: str = "dependency_failure",
        metadata_json: str = "{}",
    ) -> dict:
        self._ensure_dependency(dependency_id)
        observation = DependencyHealthObservation(
            dependency_id=dependency_id,
            status=DependencyHealthStatus.FAILURE,
            failure_type=failure_type,
            latency_ms=float(latency_ms),
            detail=detail,
            metadata=parse_json(metadata_json, {}),
        )
        self.store.append("runtime_dependency_health", observation.to_row())
        breaker = self._latest_breaker_or_closed(dependency_id)
        previous = circuit_state_from(breaker["state"])
        failure_count = int(breaker.get("failure_count") or 0) + 1
        threshold = int(breaker.get("threshold") or 3)
        next_state = CircuitState.OPEN if previous in {CircuitState.OPEN, CircuitState.HALF_OPEN} or failure_count >= threshold else previous
        reason = f"{failure_type}:{detail}"
        snapshot = self._append_breaker(dependency_id, next_state, previous, failure_count, 0, reason, threshold=threshold)
        event = self._append_event(dependency_id, DependencyEventType.FAILURE_DETECTED, next_state, "S2", reason)
        result = {"status": "ok", "health": observation.to_row(), "circuit_breaker": snapshot, "event": event}
        if next_state == CircuitState.OPEN:
            result["open_event"] = self._append_event(dependency_id, DependencyEventType.CIRCUIT_OPENED, CircuitState.OPEN, "S3", "failure_threshold_reached")
            result.update(self._select_fallback_or_isolate(dependency_id, reason))
        return result

    def open_circuit(self, dependency_id: str, reason: str = "manual_open") -> dict:
        self._ensure_dependency(dependency_id)
        breaker = self._latest_breaker_or_closed(dependency_id)
        previous = circuit_state_from(breaker["state"])
        snapshot = self._append_breaker(dependency_id, CircuitState.OPEN, previous, int(breaker.get("failure_count") or 0), 0, reason)
        result = {"status": "ok", "circuit_breaker": snapshot}
        result.update(self._select_fallback_or_isolate(dependency_id, reason))
        return result

    def half_open_circuit(self, dependency_id: str, reason: str = "cooldown_elapsed") -> dict:
        self._ensure_dependency(dependency_id)
        breaker = self._latest_breaker_or_closed(dependency_id)
        previous = circuit_state_from(breaker["state"])
        if previous != CircuitState.OPEN:
            transition = CircuitTransition(dependency_id, previous, CircuitState.HALF_OPEN, False, "half_open_requires_open_state")
            self.store.append("runtime_circuit_transitions", transition.to_row())
            return {"status": "blocked", "transition": transition.to_row(), "circuit_breaker": breaker}
        snapshot = self._append_breaker(dependency_id, CircuitState.HALF_OPEN, previous, int(breaker.get("failure_count") or 0), 0, reason)
        return {"status": "ok", "circuit_breaker": snapshot}

    def close_circuit(self, dependency_id: str, reason: str = "manual_close") -> dict:
        self._ensure_dependency(dependency_id)
        breaker = self._latest_breaker_or_closed(dependency_id)
        previous = circuit_state_from(breaker["state"])
        snapshot = self._append_breaker(dependency_id, CircuitState.CLOSED, previous, 0, int(breaker.get("success_count") or 0), reason)
        return {"status": "ok", "circuit_breaker": snapshot}

    def latest_health(self, limit: int = 50) -> dict:
        rows = self.store.fetchall_dict("SELECT * FROM runtime_dependency_health ORDER BY observed_at DESC LIMIT ?", [max(int(limit), 1)])
        return {"status": "ok", "items": rows, "dependency_health_summary": {"health_count": len(rows)}}

    def latest_breakers(self, limit: int = 50) -> dict:
        rows = self.store.fetchall_dict("SELECT * FROM runtime_circuit_breakers ORDER BY updated_at DESC LIMIT ?", [max(int(limit), 1)])
        return {"status": "ok", "items": rows, "circuit_breaker_summary": {"breaker_count": len(rows)}}

    def circuit_breaker(self, dependency_id: str) -> dict:
        return {"status": "ok", "circuit_breaker": self._latest_breaker_or_closed(dependency_id)}

    def latest_isolation(self, limit: int = 50) -> dict:
        rows = self.store.fetchall_dict(
            "SELECT * FROM runtime_dependency_events WHERE event_type = 'ISOLATED' ORDER BY created_at DESC LIMIT ?",
            [max(int(limit), 1)],
        )
        return {"status": "ok", "items": rows, "dependency_isolation_summary": {"isolation_count": len(rows)}}

    def latest_fallback_routes(self, limit: int = 50) -> dict:
        rows = self.store.fetchall_dict("SELECT * FROM runtime_fallback_routes ORDER BY created_at DESC LIMIT ?", [max(int(limit), 1)])
        return {"status": "ok", "items": rows, "fallback_route_summary": {"route_count": len(rows)}}

    def schedule_probe(self, dependency_id: str, metadata_json: str = "{}") -> dict:
        self._ensure_dependency(dependency_id)
        breaker = self._latest_breaker_or_closed(dependency_id)
        state = circuit_state_from(breaker["state"])
        probe = RecoveryProbe(dependency_id=dependency_id, circuit_state=state, probe_status=ProbeStatus.SCHEDULED, metadata=parse_json(metadata_json, {}))
        self.store.append("runtime_recovery_probes", probe.to_row())
        event = self._append_event(dependency_id, DependencyEventType.RECOVERY_PROBE_SCHEDULED, state, "S2", "recovery_probe_scheduled")
        return {"status": "ok", "recovery_probe": probe.to_row(), "event": event}

    def complete_probe(self, probe_id: str, success: bool = True, result_detail: str = "probe_completed", metadata_json: str = "{}") -> dict:
        probe = self.store.fetchone_dict("SELECT * FROM runtime_recovery_probes WHERE probe_id = ? ORDER BY scheduled_at DESC LIMIT 1", [probe_id])
        if not probe:
            return {"status": "not_found", "probe_id": probe_id}
        dependency_id = str(probe["dependency_id"])
        status = ProbeStatus.SUCCESS if success else ProbeStatus.FAILED
        completed = RecoveryProbe(
            dependency_id=dependency_id,
            circuit_state=circuit_state_from(probe.get("circuit_state")),
            probe_status=status,
            result_detail=result_detail,
            metadata=parse_json(metadata_json, {}),
            scheduled_at=str(probe.get("scheduled_at") or utc_now_iso()),
            completed_at=utc_now_iso(),
            probe_id=probe_id,
        )
        self.store.append("runtime_recovery_probes", completed.to_row())
        if success:
            breaker = self.close_circuit(dependency_id, "recovery_probe_success")["circuit_breaker"]
            event = self._append_event(dependency_id, DependencyEventType.RECOVERY_SUCCEEDED, CircuitState.CLOSED, "S0", result_detail)
        else:
            breaker = self.open_circuit(dependency_id, "recovery_probe_failed")["circuit_breaker"]
            event = self._append_event(dependency_id, DependencyEventType.RECOVERY_FAILED, CircuitState.OPEN, "S3", result_detail)
        return {"status": "ok", "recovery_probe": completed.to_row(), "circuit_breaker": breaker, "event": event}

    def latest_probes(self, limit: int = 50) -> dict:
        rows = self.store.fetchall_dict("SELECT * FROM runtime_recovery_probes ORDER BY scheduled_at DESC LIMIT ?", [max(int(limit), 1)])
        return {"status": "ok", "items": rows, "recovery_probe_summary": {"probe_count": len(rows)}}

    def _ensure_dependency(self, dependency_id: str) -> None:
        if not self._dependency_row(dependency_id):
            self.register_dependency(dependency_id=dependency_id, dependency_type="INTERNAL_API", name=dependency_id, owner="auto_registry")

    def _dependency_row(self, dependency_id: str) -> dict | None:
        return self.store.fetchone_dict(
            "SELECT * FROM runtime_dependency_registry WHERE dependency_id = ? ORDER BY registered_at DESC LIMIT 1",
            [dependency_id],
        )

    def _latest_health(self, dependency_id: str) -> dict | None:
        return self.store.fetchone_dict("SELECT * FROM runtime_dependency_health WHERE dependency_id = ? ORDER BY observed_at DESC LIMIT 1", [dependency_id])

    def _latest_breaker(self, dependency_id: str) -> dict | None:
        return self.store.fetchone_dict("SELECT * FROM runtime_circuit_breakers WHERE dependency_id = ? ORDER BY updated_at DESC LIMIT 1", [dependency_id])

    def _latest_breaker_or_closed(self, dependency_id: str) -> dict:
        return self._latest_breaker(dependency_id) or self._append_breaker(dependency_id, CircuitState.CLOSED, CircuitState.CLOSED, 0, 0, "default_closed")

    def _latest_fallback(self, dependency_id: str) -> dict | None:
        return self.store.fetchone_dict("SELECT * FROM runtime_fallback_routes WHERE dependency_id = ? ORDER BY created_at DESC LIMIT 1", [dependency_id])

    def _append_breaker(
        self,
        dependency_id: str,
        next_state: CircuitState,
        previous_state: CircuitState,
        failure_count: int,
        success_count: int,
        reason: str,
        threshold: int = 3,
    ) -> dict:
        transition = CircuitTransition(dependency_id, previous_state, next_state, True, reason)
        snapshot = CircuitBreakerSnapshot(
            dependency_id=dependency_id,
            state=next_state,
            failure_count=failure_count,
            success_count=success_count,
            threshold=threshold,
            cooldown_sec=30,
            reason=reason,
            metadata={"previous_state": previous_state.value},
        )
        self.store.append("runtime_circuit_transitions", transition.to_row())
        self.store.append("runtime_circuit_breakers", snapshot.to_row())
        return snapshot.to_row()

    def _append_event(self, dependency_id: str, event_type: DependencyEventType, state: CircuitState, severity: str, reason: str, fallback_dependency_id: str = "") -> dict:
        event = DependencyEvent(dependency_id, event_type, state, severity, reason, fallback_dependency_id)
        self.store.append("runtime_dependency_events", event.to_row())
        return event.to_row()

    def _select_fallback_or_isolate(self, dependency_id: str, reason: str) -> dict:
        dependency = self._dependency_row(dependency_id) or {}
        fallback_id = str(dependency.get("fallback_dependency_id") or "")
        if fallback_id:
            route = FallbackRoute(dependency_id, fallback_id, "ACTIVE", reason)
            self.store.append("runtime_fallback_routes", route.to_row())
            event = self._append_event(dependency_id, DependencyEventType.FALLBACK_SELECTED, CircuitState.OPEN, "S2", reason, fallback_id)
            return {"fallback_route": route.to_row(), "fallback_event": event}
        event = self._append_event(dependency_id, DependencyEventType.ISOLATED, CircuitState.OPEN, "S3", "no_fallback_available")
        return {"isolation_event": event}
