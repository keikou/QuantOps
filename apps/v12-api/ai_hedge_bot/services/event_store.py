from __future__ import annotations

import json
from typing import Any

from ai_hedge_bot.core.ids import new_cycle_id


def append_truth_event(
    store,
    *,
    event_type: str,
    aggregate_type: str,
    aggregate_id: str,
    payload: dict[str, Any],
    as_of: str,
    venue_id: str | None = None,
    account_id: str | None = None,
    instrument_id: str | None = None,
) -> None:
    """
    Minimal event sourcing helper for Sprint6H completion.
    Assumes the backing store has an 'append' method compatible with runtime_store.
    """
    row = {
        "event_id": new_cycle_id(),
        "event_type": event_type,
        "aggregate_type": aggregate_type,
        "aggregate_id": aggregate_id,
        "venue_id": venue_id,
        "account_id": account_id,
        "instrument_id": instrument_id,
        "event_time": as_of,
        "payload_json": json.dumps(payload, ensure_ascii=False, sort_keys=True),
        "version": 1,
    }
    store.append("event_store", row)