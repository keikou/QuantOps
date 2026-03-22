from __future__ import annotations


def normalize_payload(payload: dict) -> dict:
    return {str(k).lower(): v for k, v in payload.items()}
