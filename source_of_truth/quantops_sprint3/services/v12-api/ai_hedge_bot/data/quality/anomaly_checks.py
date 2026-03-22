from __future__ import annotations


def detect_outlier(value: float, threshold: float = 10.0) -> bool:
    return abs(value) > threshold
