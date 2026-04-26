from __future__ import annotations

from ai_hedge_bot.app.container import CONTAINER
from ai_hedge_bot.runtime_health.control_engine import RuntimeControlEngine
from ai_hedge_bot.runtime_health.degradation_detector import DegradationDetector
from ai_hedge_bot.runtime_health.health_collector import HealthCollector
from ai_hedge_bot.runtime_health.health_evaluator import RuntimeHealthEvaluator
from ai_hedge_bot.runtime_health.models import HealthSignal
from ai_hedge_bot.runtime_health.recovery_manager import RecoveryManager


class RuntimeHealthService:
    def __init__(self) -> None:
        self.store = CONTAINER.runtime_store
        self.collector = HealthCollector()
        self.evaluator = RuntimeHealthEvaluator()
        self.detector = DegradationDetector()
        self.control_engine = RuntimeControlEngine()
        self.recovery_manager = RecoveryManager()

    def ingest_and_evaluate(self, signals: list[HealthSignal]) -> dict:
        if not signals:
            signals = self.collector.default_probe()
        self.store.append("runtime_health_signals", [signal.to_row() for signal in signals])
        snapshot = self.evaluator.evaluate_system(signals)
        self.store.append("runtime_health_snapshots", snapshot.to_row())
        self.store.append("runtime_health_scores", [score.to_row(snapshot.snapshot_id) for score in snapshot.components])
        events = self.detector.detect(snapshot)
        actions = []
        recoveries = []
        for event in events:
            self.store.append("runtime_degradation_events", event.to_row())
            action = self.control_engine.action_for_event(event)
            recovery = self.recovery_manager.create_recovery_attempt(event)
            self.store.append("runtime_control_actions", action.to_row())
            self.store.append("runtime_recovery_attempts", recovery.to_row())
            actions.append(action.to_row())
            recoveries.append(recovery.to_row())
        return {
            "status": "ok",
            "snapshot": snapshot.to_row(),
            "component_scores": [score.to_row(snapshot.snapshot_id) for score in snapshot.components],
            "degradation_events": [event.to_row() for event in events],
            "control_actions": actions,
            "recovery_attempts": recoveries,
        }

    def ingest_json(self, signals_json: str = "[]") -> dict:
        return self.ingest_and_evaluate(self.collector.from_payload(signals_json))

    def latest(self) -> dict:
        row = self.store.fetchone_dict("SELECT * FROM runtime_health_snapshots ORDER BY created_at DESC LIMIT 1")
        if not row:
            return self.ingest_and_evaluate(self.collector.default_probe())
        return {"status": "ok", "snapshot": row}

    def components_latest(self, limit: int = 20) -> dict:
        rows = self.store.fetchall_dict("SELECT * FROM runtime_health_scores ORDER BY evaluated_at DESC LIMIT ?", [max(int(limit), 1)])
        return {"status": "ok", "items": rows, "component_health_summary": {"score_count": len(rows)}}

    def signals_latest(self, limit: int = 50) -> dict:
        rows = self.store.fetchall_dict("SELECT * FROM runtime_health_signals ORDER BY observed_at DESC LIMIT ?", [max(int(limit), 1)])
        return {"status": "ok", "items": rows, "runtime_health_signal_summary": {"signal_count": len(rows)}}

    def degradation_latest(self, limit: int = 20) -> dict:
        rows = self.store.fetchall_dict("SELECT * FROM runtime_degradation_events ORDER BY detected_at DESC LIMIT ?", [max(int(limit), 1)])
        return {"status": "ok", "items": rows, "degradation_summary": {"event_count": len(rows)}}

    def control_actions_latest(self, limit: int = 20) -> dict:
        rows = self.store.fetchall_dict("SELECT * FROM runtime_control_actions ORDER BY executed_at DESC LIMIT ?", [max(int(limit), 1)])
        return {"status": "ok", "items": rows, "runtime_control_summary": {"action_count": len(rows)}}

    def recovery_latest(self, limit: int = 20) -> dict:
        rows = self.store.fetchall_dict("SELECT * FROM runtime_recovery_attempts ORDER BY created_at DESC LIMIT ?", [max(int(limit), 1)])
        return {"status": "ok", "items": rows, "runtime_recovery_summary": {"recovery_count": len(rows)}}

    def trigger_safe_mode(self, reason: str = "manual_safe_mode_request") -> dict:
        event = self.detector.detect(self.evaluator.evaluate_system(self.collector.from_payload('[{"component":"INFRA","signal_type":"heartbeat_age_sec","value":260,"source":"manual_safe_mode"}]')))[0]
        event_row = event.to_row()
        action = self.control_engine.action_for_event(event)
        recovery = self.recovery_manager.create_recovery_attempt(event)
        self.store.append("runtime_degradation_events", {**event_row, "reason": reason})
        self.store.append("runtime_control_actions", action.to_row())
        self.store.append("runtime_recovery_attempts", recovery.to_row())
        return {"status": "ok", "degradation_event": {**event_row, "reason": reason}, "control_action": action.to_row(), "recovery_attempt": recovery.to_row()}

