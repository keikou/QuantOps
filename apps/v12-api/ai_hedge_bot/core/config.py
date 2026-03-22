from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from ai_hedge_bot.core.enums import Mode
from ai_hedge_bot.core.settings import SETTINGS


@dataclass(frozen=True)
class AppConfig:
    mode: Mode
    runtime_dir: Path
    symbols: list[str]
    data_db_path: Path

    @classmethod
    def from_settings(cls) -> 'AppConfig':
        raw_mode = getattr(SETTINGS, 'mode', 'paper')
        try:
            mode = Mode(raw_mode)
        except ValueError:
            mode = Mode.PAPER
        runtime_dir = Path(getattr(SETTINGS, 'runtime_dir'))
        data_db_path = runtime_dir / 'analytics.duckdb'
        return cls(mode=mode, runtime_dir=runtime_dir, symbols=list(getattr(SETTINGS, 'symbols', [])), data_db_path=data_db_path)
