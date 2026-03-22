from __future__ import annotations

from ai_hedge_bot.core.enums import Mode


class ModeController:
    def __init__(self, default_mode: Mode) -> None:
        self._mode = default_mode

    def get_mode(self) -> Mode:
        return self._mode

    def set_mode(self, mode: Mode) -> Mode:
        self._mode = mode
        return self._mode
