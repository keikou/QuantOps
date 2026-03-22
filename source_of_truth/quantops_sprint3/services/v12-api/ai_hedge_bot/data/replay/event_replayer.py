from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ReplayRequest:
    start: str | None = None
    end: str | None = None
    symbol: str | None = None


class EventReplayer:
    def replay(self, request: ReplayRequest) -> dict:
        return {'status': 'ok', 'request': request.__dict__, 'events_loaded': 0}
