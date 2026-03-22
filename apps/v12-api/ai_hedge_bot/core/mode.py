from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum


class RuntimeMode(str, Enum):
    PAPER = 'paper'
    SHADOW = 'shadow'
    LIVE_READY = 'live_ready'

    @classmethod
    def parse(cls, value: str | None) -> 'RuntimeMode':
        if not value:
            return cls.PAPER
        normalized = str(value).strip().lower()
        for member in cls:
            if member.value == normalized:
                return member
        raise ValueError(f'Unsupported runtime mode: {value}')


@dataclass(slots=True, frozen=True)
class ModePolicy:
    mode: str
    allow_market_data_live: bool
    allow_virtual_fills: bool
    allow_external_send: bool
    allow_state_commit: bool
    allow_shadow_latency_model: bool
    require_live_credentials: bool
    require_hard_risk_pass: bool

    def to_dict(self) -> dict:
        return asdict(self)
