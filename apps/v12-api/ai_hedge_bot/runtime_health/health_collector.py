from __future__ import annotations

from ai_hedge_bot.runtime_health.models import HealthSignal, component_from, parse_json, signal_type_from


class HealthCollector:
    def from_payload(self, signals_json: str) -> list[HealthSignal]:
        raw = parse_json(signals_json, [])
        if isinstance(raw, dict):
            raw = [raw]
        signals: list[HealthSignal] = []
        for item in raw or []:
            signals.append(
                HealthSignal(
                    component=component_from(str(item.get("component") or "INFRA")),
                    signal_type=signal_type_from(str(item.get("signal_type") or "heartbeat_age_sec")),
                    value=float(item.get("value") or 0.0),
                    source=str(item.get("source") or "runtime_health_api"),
                    metadata=item.get("metadata") or {},
                )
            )
        return signals

    def default_probe(self) -> list[HealthSignal]:
        return [
            HealthSignal(component=component_from("DATA_FEED"), signal_type=signal_type_from("data_freshness_sec"), value=1.0, source="default_probe"),
            HealthSignal(component=component_from("EXECUTION"), signal_type=signal_type_from("latency_ms"), value=50.0, source="default_probe"),
            HealthSignal(component=component_from("RISK"), signal_type=signal_type_from("error_rate"), value=0.0, source="default_probe"),
            HealthSignal(component=component_from("INFRA"), signal_type=signal_type_from("heartbeat_age_sec"), value=1.0, source="default_probe"),
        ]

