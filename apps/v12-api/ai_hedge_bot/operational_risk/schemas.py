from __future__ import annotations

from dataclasses import dataclass


RISK_LEVEL_ORDER = {
    "L0_NORMAL": 0,
    "L1_WATCH": 1,
    "L2_REDUCE": 2,
    "L3_FREEZE": 3,
    "L4_PARTIAL_HALT": 4,
    "L5_GLOBAL_HALT": 5,
}


@dataclass(frozen=True)
class TelemetryPoint:
    domain: str
    metric_name: str
    metric_value: float
    baseline_value: float
    threshold_value: float
    entity_id: str
    critical: bool = False

