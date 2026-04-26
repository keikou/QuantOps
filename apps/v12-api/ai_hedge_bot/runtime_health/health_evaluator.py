from __future__ import annotations

from collections import defaultdict

from ai_hedge_bot.core.ids import new_run_id
from ai_hedge_bot.runtime_health.models import ComponentHealthScore, HealthComponent, HealthSignal, HealthSignalType, SeverityLevel, SystemHealthSnapshot


class RuntimeHealthEvaluator:
    DEFAULT_WEIGHTS = {
        HealthSignalType.LATENCY_MS: 0.20,
        HealthSignalType.ERROR_RATE: 0.25,
        HealthSignalType.DATA_FRESHNESS_SEC: 0.20,
        HealthSignalType.QUEUE_LAG: 0.15,
        HealthSignalType.EXECUTION_FAILURE_RATE: 0.25,
        HealthSignalType.HEARTBEAT_AGE_SEC: 0.15,
    }

    def normalize_signal(self, signal: HealthSignal) -> float:
        value = max(float(signal.value), 0.0)
        if signal.signal_type == HealthSignalType.LATENCY_MS:
            return max(0.0, 1.0 - min(value / 5000.0, 1.0))
        if signal.signal_type == HealthSignalType.ERROR_RATE:
            return max(0.0, 1.0 - min(value / 0.20, 1.0))
        if signal.signal_type == HealthSignalType.DATA_FRESHNESS_SEC:
            return max(0.0, 1.0 - min(value / 600.0, 1.0))
        if signal.signal_type == HealthSignalType.QUEUE_LAG:
            return max(0.0, 1.0 - min(value / 10000.0, 1.0))
        if signal.signal_type == HealthSignalType.EXECUTION_FAILURE_RATE:
            return max(0.0, 1.0 - min(value / 0.10, 1.0))
        if signal.signal_type == HealthSignalType.HEARTBEAT_AGE_SEC:
            return max(0.0, 1.0 - min(value / 300.0, 1.0))
        return 0.5

    def severity_for_score(self, score: float) -> SeverityLevel:
        if score >= 0.90:
            return SeverityLevel.S0
        if score >= 0.70:
            return SeverityLevel.S1
        if score >= 0.50:
            return SeverityLevel.S2
        if score >= 0.30:
            return SeverityLevel.S3
        return SeverityLevel.S4

    def evaluate_components(self, signals: list[HealthSignal]) -> list[ComponentHealthScore]:
        grouped: dict[HealthComponent, list[HealthSignal]] = defaultdict(list)
        for signal in signals:
            grouped[signal.component].append(signal)
        scores: list[ComponentHealthScore] = []
        for component, component_signals in grouped.items():
            weighted_sum = 0.0
            weight_total = 0.0
            for signal in component_signals:
                weight = self.DEFAULT_WEIGHTS.get(signal.signal_type, 0.10)
                weighted_sum += self.normalize_signal(signal) * weight
                weight_total += weight
            score = weighted_sum / weight_total if weight_total else 0.0
            severity = self.severity_for_score(score)
            scores.append(ComponentHealthScore(component, score, severity, component_signals, f"{component.value} health_score={score:.4f} severity={severity.value}"))
        return scores

    def evaluate_system(self, signals: list[HealthSignal]) -> SystemHealthSnapshot:
        component_scores = self.evaluate_components(signals)
        system_score = min((score.score for score in component_scores), default=0.0)
        return SystemHealthSnapshot(
            snapshot_id=new_run_id().replace("run_", "health_snapshot_", 1),
            system_score=system_score,
            severity=self.severity_for_score(system_score),
            components=component_scores,
        )

