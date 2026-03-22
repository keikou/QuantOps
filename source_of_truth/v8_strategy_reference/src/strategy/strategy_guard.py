def guard_signal(forecast: dict) -> bool:
    return forecast["confidence"] >= 0.25
