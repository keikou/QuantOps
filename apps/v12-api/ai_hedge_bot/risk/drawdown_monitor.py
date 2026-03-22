from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class DrawdownState:
    peak_equity: float
    current_equity: float
    drawdown: float


class DrawdownMonitor:
    def update_peak_equity(self, previous_peak: float, current_equity: float) -> float:
        if previous_peak <= 0:
            return current_equity
        return max(previous_peak, current_equity)

    def calculate_drawdown(self, peak_equity: float, current_equity: float) -> float:
        if peak_equity <= 0:
            return 0.0
        return max(0.0, (peak_equity - current_equity) / peak_equity)

    def build_state(self, previous_peak: float, current_equity: float) -> DrawdownState:
        peak = self.update_peak_equity(previous_peak=previous_peak, current_equity=current_equity)
        return DrawdownState(
            peak_equity=peak,
            current_equity=current_equity,
            drawdown=self.calculate_drawdown(peak_equity=peak, current_equity=current_equity),
        )
