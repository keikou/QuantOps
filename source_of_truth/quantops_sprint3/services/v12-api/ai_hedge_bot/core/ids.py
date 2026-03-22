from __future__ import annotations

from datetime import datetime, UTC
from uuid import uuid4


def _make_id(prefix: str) -> str:
    ts = datetime.now(UTC).strftime('%Y%m%d%H%M%S')
    return f'{prefix}_{ts}_{uuid4().hex[:8]}'


def new_run_id() -> str:
    return _make_id('run')


def new_cycle_id() -> str:
    return _make_id('cycle')


def new_signal_id() -> str:
    return _make_id('sig')
